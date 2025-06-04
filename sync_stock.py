import os
import requests
import json
from dotenv import load_dotenv
from discord_notify import send_discord_message
from categorization import get_tags_for_product

# Carregar variáveis de ambiente do GitHub Actions
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
        print(f"🔍 DEBUG: Requesting Suprides API for EAN {ean}")
        print(f"URL: {url}")
        print(f"Params: user={params['user']}, *** EAN={params['EAN']}")
        print(f"Headers: Authorization=***")
        response = requests.get(url, headers=headers, params=params)
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

def parse_stock_quantity(stock_string):
    if stock_string is None:
        return 0
    if "> 10" in stock_string:
        return 20
    elif "< 10" in stock_string:
        return 5
    elif "Esgotado" in stock_string:
        return 0
    return 1

def main():
    # 🧾 Ler lista de EANs com caminho real
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "productslist.txt")
    print(f"📁 A ler productslist.txt a partir de: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print("❌ Ficheiro productslist.txt não encontrado!")
        return

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.split(":")
        ean = parts[0].strip()
        custom_price = parts[1].strip() if len(parts) > 1 else None

        suprides_product = get_suprides_product(ean)
        if not suprides_product:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"
            send_discord_message(DISCORD_WEBHOOK_URL, msg)
            continue

        title = suprides_product.get("name", "Produto sem nome")
        description = suprides_product.get("description", "")
        price = float(suprides_product.get("pvpr", 0))
        price_to_use = float(custom_price) if custom_price else price
        images = suprides_product.get("images", [])
        tags = get_tags_for_product(suprides_product)
        stock_quantity = parse_stock_quantity(suprides_product.get("stock"))

        # Criar payload Shopify
        payload = {
            "product": {
                "title": title,
                "body_html": description,
                "vendor": suprides_product.get("brand", ""),
                "tags": ", ".join(tags),
                "product_type": suprides_product.get("family", "Sem tipo"),
                "variants": [{
                    "price": price_to_use,
                    "sku": suprides_product.get("sku", ""),
                    "barcode": ean,
                    "inventory_quantity": stock_quantity,
                    "inventory_management": "shopify",
                    "inventory_policy": "deny"
                }],
                "images": [{"src": img} for img in images]
            }
        }

        # Enviar para Shopify
        shopify_url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
        try:
            response = requests.post(shopify_url, headers=shopify_headers, json=payload)
            if response.status_code in [200, 201]:
                print(f"✅ Produto criado na Shopify: {title}")
            else:
                print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exceção ao criar produto Shopify: {str(e)}")

if __name__ == "__main__":
    main()
