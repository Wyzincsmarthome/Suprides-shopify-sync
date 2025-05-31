import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

# Shopify credentials
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')

# Suprides credentials
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')
SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')

# Discord webhook
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def get_product_from_suprides(ean):
    url = "https://www.suprides.pt/rest/V1/integration/products-list"
    params = {
        'user': SUPRIDES_USER,
        'password': SUPRIDES_PASSWORD,
        'EAN': ean
    }
    headers = {
        'Authorization': f'Bearer {SUPRIDES_BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, params=params, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        else:
            return None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None

def create_or_update_product_on_shopify(product_data, custom_price=None):
    url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"

    images = [{"src": img} for img in product_data.get('images', [])]
    tags = f"{product_data.get('brand', '')}, {product_data.get('family', '')}, {product_data.get('sub_family', '')}"

    product_payload = {
        "product": {
            "title": product_data.get('name'),
            "body_html": product_data.get('description', ''),
            "vendor": product_data.get('brand', ''),
            "tags": tags,
            "variants": [{
                "sku": product_data.get('ean'),
                "price": custom_price if custom_price else product_data.get('pvpr'),
                "inventory_management": "shopify",
                "inventory_quantity": 10  # ajusta conforme necessidade
            }],
            "images": images
        }
    }

    response = requests.post(url, json=product_payload)
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data.get('name')}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")

def main():
    with open('productslist.txt', 'r') as file:
        lines = file.readlines()

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.strip().split('/')
        ean = parts[0]
        custom_price = parts[1] if len(parts) > 1 else None

        suprides_product = get_product_from_suprides(ean)
        if suprides_product:
            create_or_update_product_on_shopify(suprides_product, custom_price)
        else:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            send_discord_message(DISCORD_WEBHOOK_URL, f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")

if __name__ == "__main__":
    main()
