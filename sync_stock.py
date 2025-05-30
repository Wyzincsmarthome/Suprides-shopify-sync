import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

SHOPIFY_BASE_URL = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-04"

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_shopify_products():
    url = f"{SHOPIFY_BASE_URL}/products.json"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar produtos da Shopify: {response.status_code}")
        print(response.text)
        return []
    return response.json().get('products', [])

def create_shopify_product(product_data):
    url = f"{SHOPIFY_BASE_URL}/products.json"
    response = requests.post(url, headers=HEADERS, json=product_data)
    if response.status_code == 201:
        print(f"✅ Produto criado: {product_data['product']['title']}")
    else:
        print(f"❌ Erro ao criar produto: {response.status_code}")
        print(response.text)

def update_shopify_product(product_id, product_data):
    url = f"{SHOPIFY_BASE_URL}/products/{product_id}.json"
    response = requests.put(url, headers=HEADERS, json=product_data)
    if response.status_code == 200:
        print(f"✅ Produto atualizado: {product_data['product']['title']}")
    else:
        print(f"❌ Erro ao atualizar produto: {response.status_code}")
        print(response.text)

def main():
    try:
        with open('productslist.txt', 'r') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"❌ Erro ao abrir productslist.txt: {str(e)}")
        return

    shopify_products = get_shopify_products()
    shopify_skus = [variant['sku'] for product in shopify_products for variant in product['variants']]

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.strip().split('/')
        ean = parts[0]
        custom_price = float(parts[1]) if len(parts) > 1 else None

        # Simulação do produto a criar (ajusta conforme a API do fornecedor)
        product_payload = {
            "product": {
                "title": f"Produto com EAN {ean}",
                "body_html": f"<strong>Descrição do produto {ean}</strong>",
                "vendor": "Fornecedor Suprides",
                "product_type": "Categoria Automática",
                "tags": [ean],
                "variants": [
                    {
                        "sku": ean,
                        "price": str(custom_price) if custom_price else "0.00"
                    }
                ]
            }
        }

        if ean in shopify_skus:
            # Atualizar produto existente
            product_to_update = next(p for p in shopify_products if any(v['sku'] == ean for v in p['variants']))
            update_shopify_product(product_to_update['id'], product_payload)
        else:
            # Criar novo produto
            create_shopify_product(product_payload)

    send_discord_message(DISCORD_WEBHOOK_URL, "✅ Sincronização Shopify concluída!")

if __name__ == "__main__":
    main()
