import os
import requests
import json
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

# Credenciais Shopify
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

# Credenciais Suprides
SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')

# Função para ler EANs do ficheiro
def read_products_list():
    with open('productslist.txt', 'r') as file:
        lines = file.readlines()
    products = []
    for line in lines:
        parts = line.strip().split('/')
        ean = parts[0]
        custom_price = float(parts[1]) if len(parts) == 2 else None
        products.append((ean, custom_price))
    return products

# Função para buscar dados do fornecedor
def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?EAN={ean}"
    headers = {"Authorization": f"Bearer {SUPRIDES_BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None

# Função para converter texto de stock em número
def parse_stock_quantity(stock_text):
    if not stock_text or "indisponível" in stock_text.lower():
        return 0
    if "> 10" in stock_text:
        return 20
    if "< 10" in stock_text:
        return 5
    try:
        return int(stock_text.split()[0])
    except:
        return 10

# Função para verificar se produto já existe no Shopify
def shopify_get_product_by_sku(sku):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json?fields=id,title,variants"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar produtos Shopify: {response.status_code}")
        return None
    products = response.json().get('products', [])
    for product in products:
        for variant in product['variants']:
            if variant['sku'] == sku:
                return product
    return None

# Função para criar produto novo no Shopify
def shopify_create_product(product_payload):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=product_payload)
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_payload['product']['title']}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")

# Função para atualizar produto existente no Shopify
def shopify_update_product(product_id, product_payload):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products/{product_id}.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.put(url, headers=headers, json=product_payload)
    if response.status_code == 200:
        print(f"🔄 Produto atualizado na Shopify: {product_payload['product']['title']}")
    else:
        print(f"❌ Erro ao atualizar produto Shopify: {response.status_code} - {response.text}")

# Função principal
def main():
    products = read_products_list()
    print(f"📦 Total de EANs no ficheiro: {len(products)}")

    for ean, custom_price in products:
        suprides_product = get_product_from_suprides(ean)
        if not suprides_product:
            msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"
            print(msg)
            send_discord_message(os.getenv('DISCORD_WEBHOOK_URL'), msg)
            continue

        stock_quantity = parse_stock_quantity(suprides_product['stock'])
        price_to_use = custom_price if custom_price else suprides_product['pvpr']

        product_payload = {
            "product": {
                "title": suprides_product['name'],
                "body_html": suprides_product['description'],
                "vendor": suprides_product['brand'] or "Fornecedor Suprides",
                "product_type": suprides_product['family'] or "Sem categoria",
                "tags": ", ".join(filter(None, [
                    suprides_product['brand'],
                    suprides_product['product_line'],
                    suprides_product['family'],
                    suprides_product['sub_family']
                ])),
                "variants": [
                    {
                        "sku": ean,
                        "price": str(price_to_use),
                        "inventory_management": "shopify",
                        "inventory_quantity": stock_quantity
                    }
                ],
                "images": [{"src": img_url} for img_url in suprides_product['images']]
            }
        }

        shopify_product = shopify_get_product_by_sku(ean)
        if shopify_product:
            shopify_update_product(shopify_product['id'], product_payload)
        else:
            shopify_create_product(product_payload)

    send_discord_message(os.getenv('DISCORD_WEBHOOK_URL'), "✅ Sincronização concluída com sucesso!")

if __name__ == "__main__":
    main()
