import requests
import os

SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
}

def get_all_shopify_products():
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-04/products.json"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("products", [])
    else:
        print(f"❌ Erro API Shopify (get): {response.status_code} - {response.text}")
        return []

def create_shopify_product(product_data):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-04/products.json"
    response = requests.post(url, headers=headers, json=product_data)
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data['product']['title']}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")
