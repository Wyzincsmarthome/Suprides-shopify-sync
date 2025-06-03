import os
import requests
import json
from discord_notify import send_discord_message
from categorization import get_tags_for_product

# 🔐 Variáveis de ambiente (definidas nos GitHub Secrets)
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SUPRIDES_BEARER = os.getenv("SUPRIDES_BEARER")
SUPRIDES_USER = os.getenv("SUPRIDES_USER")
SUPRIDES_PASSWORD = os.getenv("SUPRIDES_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ✅ Verificação das variáveis
if not all([SHOPIFY_STORE_NAME, SHOPIFY_ACCESS_TOKEN, SUPRIDES_BEARER, SUPRIDES_USER, SUPRIDES_PASSWORD, DISCORD_WEBHOOK_URL]):
    print("❌ Uma ou mais variáveis de ambiente estão ausentes:")
    print(f"SHOPIFY_STORE_NAME: {SHOPIFY_STORE_NAME}")
    print(f"SHOPIFY_ACCESS_TOKEN: {'✔️' if SHOPIFY_ACCESS_TOKEN else '❌'}")
    print(f"SUPRIDES_BEARER: {'✔️' if SUPRIDES_BEARER else '❌'}")
    print(f"SUPRIDES_USER: {SUPRIDES_USER}")
    print(f"SUPRIDES_PASSWORD: {'✔️' if SUPRIDES_PASSWORD else '❌'}")
    print(f"DISCORD_WEBHOOK_URL: {'✔️' if DISCORD_WEBHOOK_URL else '❌'}")
    exit(1)

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

    print(f"🔍 DEBUG: Requesting Suprides API for EAN {ean}")
    print(f"URL: {url}")
    print(f"Params: user={params['user']}, *** EAN={params['EAN']}")
    print(f"Headers: Authorization=***")

    try:
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

def main():
    if not os.path.exists("productslist.txt"):
        print("❌ Ficheiro 'productslist.txt' não encontrado.")
        return

    with open("productslist.txt", "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        parts = line.split(":")
        ean = parts[0].strip()
        custom_price = float(parts[1].strip()) if len(parts) == 2 else None

        suprides_product = get_suprides_product(ean)
        if not suprides_product:
            print(f"⚠ Nenhum produto encontrado na Suprides para EAN {ean}")
            send_discord_message(DISCORD_WEBHOOK_URL, f"⚠ Produto não encontrado na Suprides para EAN {ean}")
            continue

        print(f"✅ Produto encontrado: {suprides_product['name']}")
        # (Aqui deves continuar com as funções que: 
        # - verificam se o produto existe na Shopify,
        # - atualizam ou criam o produto
        # - categorizam com get_tags_for_product(...)
        # Estas funções podem estar no `shopify_api.py`, `categorization.py` e `discord_notify.py`.)

        # Exemplo de log:
        print(f"ℹ️ Preço fornecedor: {suprides_product.get('pvpr')} | Preço customizado: {custom_price if custom_price else 'N/A'}")

if __name__ == "__main__":
    main()
