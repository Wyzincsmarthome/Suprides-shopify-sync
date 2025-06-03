import os
import requests
import json
from discord_notify import send_discord_message
from categorization import get_tags_for_product

SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SUPRIDES_BEARER = os.getenv("SUPRIDES_BEARER")
SUPRIDES_USER = os.getenv("SUPRIDES_USER")
SUPRIDES_PASSWORD = os.getenv("SUPRIDES_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

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
        print(f"URL: {url}\nParams: user={params['user']}, *** EAN={ean}\nHeaders: Authorization=***")
        response = requests.get(url, headers=headers, params=params)
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        else:
            return None
    except Exception as e:
        print(f"❌ Exceção ao consultar a Suprides: {str(e)}")
        return None

def main():
    try:
        with open("productslist.txt", "r") as f:
            eans = [line.strip().split(":")[0] for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Ficheiro 'productslist.txt' não encontrado.")
        return

    print(f"\n📦 Total de EANs no ficheiro: {len(eans)}")

    for ean in eans:
        suprides_product = get_suprides_product(ean)

        if suprides_product:
            nome = suprides_product['name']
            pvpr = suprides_product['pvpr']
            stock = suprides_product['stock']
            msg = f"✅ Produto encontrado: {nome}\nEAN: {ean}\nPreço fornecedor (pvpr): {pvpr} €\nStock: {stock}"
        else:
            msg = f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}"

        send_discord_message(DISCORD_WEBHOOK_URL, msg)
        print("✅ Mensagem enviada para o Discord!")

if __name__ == "__main__":
    main()
