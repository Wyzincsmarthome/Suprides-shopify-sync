import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')

HEADERS_SHOPIFY = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

HEADERS_SUPRIDES = {
    'Authorization': f'Bearer {SUPRIDES_BEARER_TOKEN}',
    'Content-Type': 'application/json'
}

def get_shopify_product_by_sku(sku):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    response = requests.get(url, headers=HEADERS_SHOPIFY)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar produtos da Shopify: {response.status_code}")
        return None

    products = response.json().get('products', [])
    for product in products:
        for variant in product['variants']:
            if variant['sku'] == sku:
                return product
    return None

def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?EAN={ean}"
    response = requests.get(url, headers=HEADERS_SUPRIDES)
    if response.status_code != 200:
        print(f"❌ Erro ao acessar API Suprides: {response.status_code}")
        return None

    data = response.json()
    if not data or not isinstance(data, list) or 'status' in data[0]:
        return None

    return data[0]

def create_product_on_shopify(product_data):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    response = requests.post(url, headers=HEADERS_SHOPIFY, json=product_data)
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data['product']['title']}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")

def update_product_on_shopify(product_id, product_data):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products/{product_id}.json"
    response = requests.put(url, headers=HEADERS_SHOPIFY, json=product_data)
    if response.status_code == 200:
        print(f"✅ Produto atualizado na Shopify: {product_data['product']['title']}")
    else:
        print(f"❌ Erro ao atualizar produto Shopify: {response.status_code} - {response.text}")

def sync_shopify_products():
    with open('productslist.txt', 'r') as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.split('/')
        ean = parts[0]
        custom_price = float(parts[1]) if len(parts) == 2 else None

        suprides_product = get_product_from_suprides(ean)
        if not suprides_product:
            msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"
            print(msg)
            send_discord_message(DISCORD_WEBHOOK_URL, msg)
            continue

        name = suprides_product.get('name')
        supplier_price = custom_price if custom_price else suprides_product.get('pvpr')
        description = suprides_product.get('description', '')
        images = [{'src': img} for img in suprides_product.get('images', [])]

        existing_product = get_shopify_product_by_sku(ean)

        product_payload = {
            'product': {
                'title': name,
                'body_html': description,
                'variants': [{
                    'sku': ean,
                    'price': supplier_price,
                    'inventory_quantity': 10,
                    'inventory_management': 'shopify'
                }],
                'images': images
            }
        }

        if existing_product:
            update_product_on_shopify(existing_product['id'], product_payload)
        else:
            create_product_on_shopify(product_payload)

if __name__ == "__main__":
    try:
        sync_shopify_products()
        print("✅ Sincronização concluída!")
    except Exception as e:
        print(f"❌ Erro durante a sincronização: {e}")
