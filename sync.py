import os
import requests
from dotenv import load_dotenv
from discord_notify import send_discord_message

load_dotenv()

# Suprides credentials
SUPRIDES_BEARER_TOKEN = os.getenv('SUPRIDES_BEARER_TOKEN')
SUPRIDES_USER = os.getenv('SUPRIDES_USER')
SUPRIDES_PASSWORD = os.getenv('SUPRIDES_PASSWORD')

# Shopify credentials
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')

# Discord webhook
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Shopify API base and headers
SHOPIFY_API_BASE = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-04"
SHOPIFY_HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# Listas principais
CASA_INTELIGENTE_LIST = [
    "Assistentes Virtuais", "Campainha Inteligente", "Controlo Remoto",
    "Fechaduras Inteligentes", "Hubs Inteligentes", "Iluminação",
    "Interruptor Inteligente", "Motor Cortinas", "Painel Controlo",
    "Termostato Inteligente", "Tomadas", "Gadgets Inteligentes"
]

GADGETS_LIST = [
    "Aspiradores", "Aspirador Vertical", "Aspirador Robô", "Mini Aspirador", "Acessórios Aspiradores",
    "Auscultadores", "Cozinha", "Smartwatch", "Gadgets P/ Animais", "Gadgets Diversos"
]

def get_product_from_suprides(ean):
    url = f"https://www.suprides.pt/rest/V1/integration/products-list?user={SUPRIDES_USER}&password={SUPRIDES_PASSWORD}&EAN={ean}"
    headers = {
        "Authorization": f"Bearer {SUPRIDES_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    else:
        print(f"❌ Erro API Suprides ({response.status_code}): {response.text}")
        return None

def get_shopify_product_by_ean(ean):
    url = f"{SHOPIFY_API_BASE}/products.json"
    response = requests.get(url, headers=SHOPIFY_HEADERS)
    if response.status_code == 200:
        products = response.json().get('products', [])
        for product in products:
            for variant in product['variants']:
                if variant.get('sku') == ean:
                    return product, variant
        return None, None
    else:
        print(f"❌ Erro API Shopify ({response.status_code}): {response.text}")
        return None, None

def create_shopify_product(product_data, ean, price, stock, description, images, tags):
    url = f"{SHOPIFY_API_BASE}/products.json"
    payload = {
        "product": {
            "title": product_data['name'],
            "body_html": description,
            "vendor": product_data.get('brand', 'Fornecedor'),
            "product_type": product_data.get('family', 'Categoria'),
            "tags": tags,
            "variants": [{
                "sku": ean,
                "price": price,
                "inventory_management": "shopify",
                "inventory_quantity": stock
            }],
            "images": [{"src": img} for img in images]
        }
    }
    response = requests.post(url, json=payload, headers=SHOPIFY_HEADERS)
    if response.status_code == 201:
        print(f"✅ Produto criado na Shopify: {product_data['name']}")
    else:
        print(f"❌ Erro ao criar produto Shopify: {response.status_code} - {response.text}")

def update_shopify_product(product_id, variant_id, price, stock, description, images, tags, product_type):
    product_url = f"{SHOPIFY_API_BASE}/products/{product_id}.json"
    product_payload = {
        "product": {
            "id": product_id,
            "body_html": description,
            "product_type": product_type,
            "tags": tags,
            "images": [{"src": img} for img in images]
        }
    }
    requests.put(product_url, json=product_payload, headers=SHOPIFY_HEADERS)

    variant_url = f"{SHOPIFY_API_BASE}/variants/{variant_id}.json"
    variant_payload = {
        "variant": {
            "id": variant_id,
            "price": price,
            "inventory_quantity": stock
        }
    }
    response = requests.put(variant_url, json=variant_payload, headers=SHOPIFY_HEADERS)
    if response.status_code == 200:
        print(f"✅ Produto atualizado na Shopify (ID {product_id})")
    else:
        print(f"❌ Erro ao atualizar produto Shopify: {response.status_code} - {response.text}")

def parse_stock_quantity(stock_text):
    if not stock_text or "disponível" not in stock_text.lower():
        return 0
    if "< 10" in stock_text:
        return 5
    if "> 10" in stock_text:
        return 20
    return 10

def build_tags(product_data, categoria_principal):
    tags = set()
    if product_data.get('brand'):
        tags.add(product_data['brand'].strip())
    if product_data.get('family'):
        tags.add(product_data['family'].strip())
    if product_data.get('sub_family'):
        tags.add(product_data['sub_family'].strip())
    if categoria_principal:
        tags.add(categoria_principal)
    return ", ".join(tags)

def determine_main_category(family, sub_family):
    for item in CASA_INTELIGENTE_LIST:
        if item.lower() in (family or "").lower() or item.lower() in (sub_family or "").lower():
            return "Casa Inteligente"
    for item in GADGETS_LIST:
        if item.lower() in (family or "").lower() or item.lower() in (sub_family or "").lower():
            return "Gadgets"
    return None

def main():
    if not os.path.exists('productslist.txt'):
        print("⚠ Ficheiro productslist.txt não encontrado!")
        return

    with open('productslist.txt', 'r') as file:
        lines = file.readlines()

    print(f"📦 Total de EANs no ficheiro: {len(lines)}")

    for line in lines:
        clean_line = line.strip()
        if '/' in clean_line:
            parts = clean_line.split('/')
        elif ':' in clean_line:
            parts = clean_line.split(':')
        else:
            parts = [clean_line]

        ean = parts[0]
        custom_price = float(parts[1]) if len(parts) == 2 else None

        product_data = get_product_from_suprides(ean)
        if not product_data:
            continue

        price = custom_price if custom_price else float(product_data['pvpr'])
        stock = parse_stock_quantity(product_data['stock'])
        description = product_data.get('description', '')
        images = product_data.get('images', [])
        product_type = product_data.get('family', 'Categoria')

        categoria_principal = determine_main_category(product_data.get('family'), product_data.get('sub_family'))
        if not categoria_principal:
            msg = f"⚠ Produto sem categoria principal: {product_data['name']} (EAN: {ean})"
            print(msg)
            send_discord_message(DISCORD_WEBHOOK_URL, msg)

        tags = build_tags(product_data, categoria_principal)

        shopify_product, shopify_variant = get_shopify_product_by_ean(ean)

        if shopify_product and shopify_variant:
            update_shopify_product(shopify_product['id'], shopify_variant['id'], price, stock, description, images, tags, product_type)
        else:
            create_shopify_product(product_data, ean, price, stock, description, images, tags)

        if stock == 0:
            send_discord_message(DISCORD_WEBHOOK_URL, f"⚠ Produto sem stock: {product_data['name']} (EAN: {ean})")

if __name__ == "__main__":
    main()
