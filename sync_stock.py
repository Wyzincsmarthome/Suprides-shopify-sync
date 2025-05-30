import os
import requests
import json
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

HEADERS_SHOPIFY = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
}

HEADERS_SUPRIDES = {
    "Authorization": f"Bearer {SUPRIDES_BEARER_TOKEN}"
}

def read_products_list():
    with open('productslist.txt', 'r') as file:
        lines = file.readlines()
    return [line.strip().split('/')[0] for line in lines]

def get_suprides_product(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?EAN={ean}"
    response = requests.get(url, headers=HEADERS_SUPRIDES)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"✅ Dados recebidos da API Suprides: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data[0]  # Assume primeiro item
        else:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            return None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None

def get_shopify_product_by_ean(ean):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    response = requests.get(url, headers=HEADERS_SHOPIFY)
    if response.status_code == 200:
        products = response.json().get('products', [])
        for product in products:
            for variant in product['variants']:
                if variant.get('sku') == ean:
                    return product
        return None
    else:
        print(f"❌ Erro API Shopify ({response.status_code}): {response.text}")
        return None

def create_or_update_shopify_product(ean, suprides_product, custom_price):
    product_payload = {
        "product": {
            "title": suprides_product.get('name', f"Produto {ean}"),
            "body_html": suprides_product.get('description', ''),
            "vendor": suprides_product.get('brand', ''),
            "product_type": suprides_product.get('family', ''),
            "tags": suprides_product.get('product_line', ''),
            "variants": [
                {
                    "sku": ean,
                    "price": custom_price if custom_price else suprides_product.get('pvpr', '0'),
                    "inventory_management": "shopify",
                    "inventory_quantity": parse_stock_quantity(suprides_product.get('stock', ''))
                }
            ],
            "images": [{"src": img} for img in suprides_product.get('images', [])]
        }
    }

    shopify_product = get_shopify_product_by_ean(ean)
    if shopify_product:
        product_id = shopify_product['id']
        url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products/{product_id}.json"
        response = requests.put(url, headers=HEADERS_SHOPIFY, json=product_payload)
        action = 'Atualizado'
    else:
        url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
        response = requests.post(url, headers=HEADERS_SHOPIFY, json=product_payload)
        action = 'Criado'

    if response.status_code in [200, 201]:
        print(f"✅ Produto {action} na Shopify: {product_payload['product']['title']}")
    else:
        print(f"❌ Erro ao {action.lower()} produto Shopify ({response.status_code}): {response.text}")

def parse_stock_quantity(stock_text):
    if not stock_text:
        return 0
    stock_text = stock_text.lower()
    if "disponível" not in stock_text:
        return 0
    if "< 10" in stock_text:
        return 5
    if "> 10" in stock_text:
        return 20
    return 10

def main():
    ean_list = read_products_list()
    print(f"📦 Total de EANs no ficheiro: {len(ean_list)}")

    for line in ean_list:
        parts = line.strip().split('/')
        ean = parts[0]
        custom_price = parts[1] if len(parts) > 1 else None

        suprides_product = get_suprides_product(ean)
        if suprides_product:
            price_to_use = custom_price if custom_price else suprides_product.get('pvpr', '0')
            create_or_update_shopify_product(ean, suprides_product, price_to_use)
        else:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")

    # Notificação final
    send_discord_message(DISCORD_WEBHOOK_URL, f"✅ Sincronização concluída para {len(ean_list)} produtos.")

if __name__ == "__main__":
    main()
