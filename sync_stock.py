import os
import requests
import json
from discord_notify import send_discord_message
from categorization import get_tags_for_product


# Credenciais das APIs
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SUPRIDES_BEARER = os.getenv("SUPRIDES_BEARER")
SUPRIDES_USER = os.getenv("SUPRIDES_USER")
SUPRIDES_PASSWORD = os.getenv("SUPRIDES_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Headers Shopify
shopify_headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
}

def get_suprides_product(ean):
    url = "https://www.suprides.pt/rest/V1/integration/products-list"
    headers = {
        "Authorization": f"Bearer {SUPRIDES_BEARER}",
        "Content-Type": "application/json"
    }
    params = {
        "user": SUPRIDES_USER,
        "password": SUPRIDES_PASSWORD,
        "EAN": ean
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"🔍 DEBUG: Requesting Suprides API for EAN {ean}")
        print(f"URL: {url}")
        print(f"Params: user={params['user']}, *** EAN={params['EAN']}")
        print(f"Headers: Authorization=***")
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        else:
            print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exceção ao consultar a Suprides: {str(e)}")
        return None

def create_product_on_shopify(product_data, tags):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    payload = {
        "product": {
            "title": product_data["name"],
            "body_html": product_data["description"],
            "vendor": product_data["brand"],
            "tags": tags,
            "product_type": product_data["family"] or "Sem categoria",
            "variants": [{
                "price": product_data["pvpr"],
                "sku": product_data["ean"],
                "inventory_management": "shopify",
                "inventory_quantity": 10,
                "requires_shipping": True
            }],
            "images": [{"src": img} for img in product_data["images"]]
        }
    }
    response = requests.post(url, headers=shopify_headers, data=json.dumps(payload))
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data['name']}")
    else:
        print(f"❌ Erro ao criar produto Shopify ({response.status_code}): {response.text}")

def main():
    with open("productslist.txt", "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.split(":")
        ean = parts[0]
        custom_price = float(parts[1]) if len(parts) > 1 else None

        suprides_product = get_suprides_product(ean)
        if not suprides_product:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            send_discord_message(DISCORD_WEBHOOK_URL, f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            continue

        price_to_use = custom_price if custom_price else suprides_product["pvpr"]
        suprides_product["pvpr"] = price_to_use
        tags = get_tags_for_product(suprides_product)
        create_product_on_shopify(suprides_product, tags)
        print("✅ Mensagem enviada para o Discord!")
        send_discord_message(DISCORD_WEBHOOK_URL, f"✅ Produto sincronizado: {suprides_product['name']} (EAN: {ean})")

if __name__ == "__main__":
    main()
