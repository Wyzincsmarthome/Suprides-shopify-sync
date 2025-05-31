import os
import requests

SUPRIDES_BEARER = os.getenv('SUPRIDES_BEARER')
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')

def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list"
    params = {
        'user': SUPRIDES_USER,
        'password': SUPRIDES_PASSWORD,
        'EAN': ean
    }
    headers = {
        'Authorization': f'Bearer {SUPRIDES_BEARER}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        else:
            return None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None
