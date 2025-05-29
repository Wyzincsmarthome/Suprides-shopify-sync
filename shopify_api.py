import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_PASSWORD = os.getenv("SHOPIFY_API_PASSWORD")
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")  # ex: 'wyzinc'

BASE_URL = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04"

def get_all_products():
    url = f"{BASE_URL}/products.json?limit=250"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('products', [])
    except Exception as e:
        print(f"Erro ao buscar produtos da Shopify: {e}")
        return []
