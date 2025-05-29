import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')

def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?user={SUPRIDES_USER}&password={SUPRIDES_PASSWORD}&EAN={ean}"
    headers = {
        "Authorization": f"Bearer {SUPRIDES_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data:
            print("✅ Dados recebidos da API Suprides:")
            print(data)
        else:
            print("⚠ Nenhum produto encontrado com este EAN.")
    else:
        print(f"❌ Erro ao acessar API Suprides: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_ean = input("Insere um EAN para testar: ")
    get_product_from_suprides(test_ean)
