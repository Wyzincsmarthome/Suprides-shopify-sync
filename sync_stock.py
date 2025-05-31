import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

# Credenciais
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')
SUPRIDES_BEARER = os.getenv('SUPRIDES_BEARER')

SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

HEADERS_SHOPIFY = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
}

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
    response = requests.get(url, params=params, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def shopify_product_exists(ean):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json?fields=id,title,variants"
    response = requests.get(url, headers=HEADERS_SHOPIFY)
    if response.status_code != 200:
        print(f"❌ Erro API Shopify (GET): {response.status_code} - {response.text}")
        return None
    products = response.json().get('products', [])
    for product in products:
        for variant in product['variants']:
            if variant['sku'] == ean:
                return product['id']
    return None

def create_or_update_shopify_product(ean, data, custom_price):
    product_payload = {
        "product": {
            "title": data['name'],
            "body_html": data['description'],
            "vendor": data['brand'],
            "product_type": data['family'],
            "tags": f"{data['brand']}, {data['family']}, {data['sub_family'] or ''}",
            "variants": [{
                "sku": ean,
                "price": custom_price if custom_price else data['pvpr'],
                "inventory_management": "shopify",
                "inventory_quantity": 10  # Exemplo fixo, pode ser ajustado conforme stock real
            }],
            "images": [{"src": img} for img in data['images']]
        }
    }

    product_id = shopify_product_exists(ean)
    if product_id:
        url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products/{product_id}.json"
        response = requests.put(url, json=product_payload, headers=HEADERS_SHOPIFY)
        action = "Atualizado"
    else:
        url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
        response = requests.post(url, json=product_payload, headers=HEADERS_SHOPIFY)
        action = "Criado"

    if response.status_code in [200, 201]:
        print(f"✅ Produto {action} no Shopify: {data['name']}")
    else:
        print(f"❌ Erro API Shopify ({action}): {response.status_code} - {response.text}")

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
            print(f"✅ Produto encontrado: {suprides_product['name']}")
            create_or_update_shopify_product(ean, suprides_product, custom_price)
        else:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            send_discord_message(DISCORD_WEBHOOK_URL, f"⚠ Atenção! Produto com EAN {ean} não encontrado no fornecedor.")

if __name__ == "__main__":
    main()
