import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

SUPRIDES_BEARER = os.getenv('SUPRIDES_BEARER')
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')

SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def get_product_from_suprides(ean):
    url = "https://www.suprides.pt/rest/V1/integration/products-list"
    params = {
        'user': SUPRIDES_USER,
        'password': SUPRIDES_PASSWORD,
        'EAN': ean
    }
    headers = {
        'Authorization': f'Bearer {SUPRIDES_BEARER}',
        'Content-Type': 'application/json'
    }

    print(f"🔍 DEBUG: Requesting Suprides API for EAN {ean}")
    print(f"URL: {url}")
    print(f"Params: user={SUPRIDES_USER}, password=***, EAN={ean}")
    print(f"Headers: Authorization=Bearer ****")

    response = requests.get(url, headers=headers, params=params)
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

def create_or_update_shopify_product(product_data, custom_price=None):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    product_payload = {
        "product": {
            "title": product_data['name'],
            "body_html": product_data['description'],
            "vendor": product_data['brand'],
            "tags": f"{product_data['brand']}, {product_data['family']}, {product_data['product_line']}",
            "variants": [
                {
                    "sku": product_data['ean'],
                    "price": custom_price if custom_price else product_data['pvpr'],
                    "inventory_quantity": 10,
                    "inventory_management": "shopify"
                }
            ],
            "images": [{"src": img} for img in product_data['images']]
        }
    }

    response = requests.post(url, headers=headers, json=product_payload)
    if response.status_code == 201:
        print(f"✅ Produto {product_data['name']} criado/atualizado na Shopify")
    else:
        print(f"❌ Erro ao criar/atualizar produto Shopify: {response.status_code} - {response.text}")

def main():
    with open('productslist.txt', 'r') as f:
        eans = [line.strip().split('/')[0] for line in f if line.strip()]

    print(f"📦 Total de EANs no ficheiro: {len(eans)}")

    for ean in eans:
        suprides_product = get_product_from_suprides(ean)
        if suprides_product:
            custom_price = None
            create_or_update_shopify_product(suprides_product, custom_price)
        else:
            msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"
            print(msg)
            send_discord_message(DISCORD_WEBHOOK_URL, msg)

if __name__ == "__main__":
    main()
