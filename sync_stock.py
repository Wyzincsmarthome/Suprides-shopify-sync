import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Shopify configs
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

# Suprides configs
SUPRIDES_BEARER = os.getenv('SUPRIDES_BEARER')

# Discord webhook
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_message(message):
    data = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("✅ Notificação enviada ao Discord.")
    else:
        print(f"❌ Erro ao enviar notificação Discord: {response.status_code}")

def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?EAN={ean}"
    headers = {"Authorization": f"Bearer {SUPRIDES_BEARER}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        products = response.json()
        if products and isinstance(products, list) and len(products) > 0:
            return products[0]
        else:
            return None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None

def shopify_product_exists(sku):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json?fields=id,title,variants"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        products = response.json().get('products', [])
        for product in products:
            for variant in product['variants']:
                if variant['sku'] == sku:
                    return True
    else:
        print(f"❌ Erro ao verificar produto Shopify: {response.status_code} - {response.text}")
    return False

def create_product_in_shopify(product_data, price_override=None):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }

    price_to_use = price_override if price_override else product_data['pvpr']
    stock_quantity = parse_stock_quantity(product_data['stock'])

    payload = {
        "product": {
            "title": product_data['name'],
            "body_html": product_data['description'],
            "vendor": product_data['brand'],
            "product_type": product_data['family'] or "Sem categoria",
            "tags": f"{product_data['brand']}, {product_data['family']}, {product_data['sub_family']}",
            "variants": [
                {
                    "price": price_to_use,
                    "sku": product_data['ean'],
                    "inventory_management": "shopify",
                    "inventory_quantity": stock_quantity
                }
            ],
            "images": [{"src": img_url} for img_url in product_data['images']]
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data['name']}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")

def parse_stock_quantity(stock_str):
    if ">" in stock_str:
        return 20
    elif "<" in stock_str:
        return 5
    elif "Esgotado" in stock_str or "Sem stock" in stock_str:
        return 0
    else:
        return 10

def main():
    if not os.path.exists("productslist.txt"):
        print("❌ Ficheiro productslist.txt não encontrado!")
        return

    with open("productslist.txt", "r") as f:
        ean_lines = [line.strip() for line in f if line.strip()]

    print(f"📦 Total de EANs no ficheiro: {len(ean_lines)}")

    for line in ean_lines:
        if "/" in line:
            ean, custom_price = line.split("/")
            custom_price = custom_price.strip()
        else:
            ean = line.strip()
            custom_price = None

        suprides_product = get_product_from_suprides(ean)
        if suprides_product:
            print(f"✅ Produto encontrado na Suprides: {suprides_product['name']}")

            if shopify_product_exists(ean):
                print(f"ℹ Produto já existe na Shopify, ignorando criação: {ean}")
            else:
                create_product_in_shopify(suprides_product, price_override=custom_price)
        else:
            warning_msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"
            print(warning_msg)
            send_discord_message(warning_msg)

if __name__ == "__main__":
    main()
