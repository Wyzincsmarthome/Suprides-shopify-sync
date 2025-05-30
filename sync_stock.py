import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def get_shopify_products():
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Erro ao buscar produtos da Shopify: {response.status_code}")
        return None
    return response.json().get('products', [])

def main():
    if not os.path.exists("productslist.txt"):
        print("❌ O ficheiro 'productslist.txt' não foi encontrado.")
        return

    with open("productslist.txt", "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    shopify_products = get_shopify_products()
    if shopify_products is None:
        print("❌ Não foi possível obter produtos da Shopify.")
        return

    for line in lines:
        ean = line.split("/")[0]
        product_found = any(
            variant['sku'] == ean or variant['barcode'] == ean
            for product in shopify_products
            for variant in product['variants']
        )

        if product_found:
            print(f"✅ Produto com EAN {ean} já existe na Shopify. Será atualizado.")
            # Aqui podes chamar a função de atualização
        else:
            print(f"➕ Produto com EAN {ean} não encontrado. Será criado.")
            # Aqui podes chamar a função de criação

if __name__ == "__main__":
    main()
