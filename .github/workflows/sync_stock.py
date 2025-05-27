#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Sincronização Automática de Stock entre Suprides e Shopify

Este script consulta a API do fornecedor Suprides para obter informações atualizadas
de stock e atualiza automaticamente os produtos correspondentes na loja Shopify.

Autor: Manus AI
Data: Maio 2025
"""

import requests
import json
import time
import os
import re
import logging
from datetime import datetime

# Configuração de logging para acompanhar a execução do script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sync_stock.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Credenciais da API do fornecedor Suprides
# Estas credenciais serão substituídas pelos segredos do GitHub
SUPRIDES_USER = os.environ.get("SUPRIDES_USER", "")
SUPRIDES_PASSWORD = os.environ.get("SUPRIDES_PASSWORD", "")
SUPRIDES_BASE_URL = "https://www.suprides.pt/rest/V1/integration/products-list"

# Credenciais da API Shopify
# Estas credenciais serão substituídas pelos segredos do GitHub
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE", "")  # exemplo: sua-loja.myshopify.com
SHOPIFY_API_KEY = os.environ.get("SHOPIFY_API_KEY", "")
SHOPIFY_API_PASSWORD = os.environ.get("SHOPIFY_API_PASSWORD", "")
SHOPIFY_API_VERSION = "2023-10"  # Versão atual da API Shopify

def get_suprides_products(page=1, limit=100):
    """
    Obtém produtos da API do fornecedor Suprides.
    
    Args:
        page (int): Número da página a consultar
        limit (int): Número máximo de produtos por página
        
    Returns:
        list: Lista de produtos ou None em caso de erro
    """
    logger.info(f"Consultando produtos da Suprides (página {page}, limite {limit})")
    
    # Construir a URL com os parâmetros
    url = f"{SUPRIDES_BASE_URL}?user={SUPRIDES_USER}&password={SUPRIDES_PASSWORD}&page={page}&limit={limit}"
    
    try:
        # Fazer a requisição GET para a API do fornecedor
        response = requests.get(url)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            products = response.json()
            logger.info(f"Obtidos {len(products)} produtos da Suprides")
            return products
        else:
            logger.error(f"Erro ao consultar API Suprides: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exceção ao consultar API Suprides: {str(e)}")
        return None

def get_suprides_product_by_ean(ean):
    """
    Obtém um produto específico da API do fornecedor Suprides pelo código EAN.
    
    Args:
        ean (str): Código EAN do produto
        
    Returns:
        dict: Dados do produto ou None em caso de erro ou produto não encontrado
    """
    logger.info(f"Consultando produto com EAN {ean} da Suprides")
    
    # Construir a URL com o parâmetro EAN
    url = f"{SUPRIDES_BASE_URL}?user={SUPRIDES_USER}&password={SUPRIDES_PASSWORD}&EAN={ean}"
    
    try:
        # Fazer a requisição GET para a API do fornecedor
        response = requests.get(url)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            products = response.json()
            if products and len(products) > 0:
                logger.info(f"Produto com EAN {ean} encontrado na Suprides")
                return products[0]
            else:
                logger.warning(f"Produto com EAN {ean} não encontrado na Suprides")
                return None
        else:
            logger.error(f"Erro ao consultar API Suprides para EAN {ean}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exceção ao consultar API Suprides para EAN {ean}: {str(e)}")
        return None

def parse_stock_status(stock_text):
    """
    Analisa o texto do campo stock da API Suprides e converte para quantidade numérica.
    
    Args:
        stock_text (str): Texto do campo stock (ex: "Disponível ( < 10 UN )")
        
    Returns:
        int: Quantidade estimada de stock
    """
    logger.info(f"Analisando status de stock: '{stock_text}'")
    
    # Se não houver texto de stock, considerar como 0
    if not stock_text or stock_text.strip() == "":
        return 0
    
    # Converter para minúsculas para facilitar a comparação
    stock_text = stock_text.lower()
    
    # Verificar se o produto está disponível
    if "disponível" not in stock_text:
        logger.info("Produto não disponível, definindo stock como 0")
        return 0
    
    # Tentar extrair quantidade numérica usando expressões regulares
    # Procurar padrões como "< 10 UN" ou "5 UN"
    quantity_match = re.search(r'(\d+)\s*un', stock_text)
    if quantity_match:
        quantity = int(quantity_match.group(1))
        logger.info(f"Quantidade extraída do texto: {quantity}")
        return quantity
    
    # Verificar se é uma quantidade limitada (< X)
    if "< 10" in stock_text:
        logger.info("Stock limitado (< 10), definindo como 5")
        return 5
    
    # Se não conseguir determinar a quantidade exata, mas estiver disponível
    # definir um valor padrão de 20 unidades
    logger.info("Produto disponível sem quantidade específica, definindo stock como 20")
    return 20

def get_shopify_products():
    """
    Obtém todos os produtos da loja Shopify.
    
    Returns:
        list: Lista de produtos ou None em caso de erro
    """
    logger.info("Consultando produtos da loja Shopify")
    
    # Construir a URL da API Shopify
    url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/products.json"
    
    all_products = []
    
    try:
        # A API Shopify usa paginação, então precisamos fazer várias requisições
        while url:
            # Fazer a requisição GET para a API Shopify
            response = requests.get(url)
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                all_products.extend(products)
                
                # Verificar se há mais páginas
                link_header = response.headers.get('Link', '')
                if 'rel="next"' in link_header:
                    # Extrair a URL da próxima página
                    url = re.search(r'<(https://[^>]+)>; rel="next"', link_header).group(1)
                else:
                    url = None
            else:
                logger.error(f"Erro ao consultar API Shopify: {response.status_code} - {response.text}")
                return None
        
        logger.info(f"Obtidos {len(all_products)} produtos da Shopify")
        return all_products
    except Exception as e:
        logger.error(f"Exceção ao consultar API Shopify: {str(e)}")
        return None

def find_shopify_product_by_ean(shopify_products, ean):
    """
    Encontra um produto Shopify pelo código EAN.
    
    Args:
        shopify_products (list): Lista de produtos Shopify
        ean (str): Código EAN a procurar
        
    Returns:
        dict: Produto encontrado ou None se não encontrado
    """
    logger.info(f"Procurando produto com EAN {ean} na Shopify")
    
    for product in shopify_products:
        # Verificar se o produto tem variantes
        variants = product.get('variants', [])
        for variant in variants:
            # O código EAN pode estar em diferentes campos, dependendo da configuração da loja
            # Verificar campos comuns onde o EAN pode estar armazenado
            barcode = variant.get('barcode', '')
            sku = variant.get('sku', '')
            
            if barcode == ean or sku == ean:
                logger.info(f"Produto com EAN {ean} encontrado na Shopify (ID: {product['id']}, Variante: {variant['id']})")
                return {'product': product, 'variant': variant}
    
    logger.warning(f"Produto com EAN {ean} não encontrado na Shopify")
    return None

def update_shopify_inventory(variant_id, inventory_item_id, new_quantity):
    """
    Atualiza o inventário de um produto na Shopify.
    
    Args:
        variant_id (int): ID da variante do produto
        inventory_item_id (int): ID do item de inventário
        new_quantity (int): Nova quantidade de stock
        
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    logger.info(f"Atualizando inventário da variante {variant_id} para {new_quantity} unidades")
    
    # Primeiro, precisamos obter os locais de inventário
    locations_url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/locations.json"
    
    try:
        # Obter locais de inventário
        locations_response = requests.get(locations_url)
        
        if locations_response.status_code != 200:
            logger.error(f"Erro ao obter locais de inventário: {locations_response.status_code} - {locations_response.text}")
            return False
        
        locations = locations_response.json().get('locations', [])
        
        if not locations:
            logger.error("Nenhum local de inventário encontrado na loja Shopify")
            return False
        
        # Usar o primeiro local de inventário (geralmente o padrão)
        location_id = locations[0]['id']
        
        # Construir a URL para atualizar o inventário
        inventory_url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/inventory_levels/set.json"
        
        # Dados para atualizar o inventário
        inventory_data = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": new_quantity
        }
        
        # Fazer a requisição POST para atualizar o inventário
        inventory_response = requests.post(inventory_url, json=inventory_data)
        
        if inventory_response.status_code == 200:
            logger.info(f"Inventário atualizado com sucesso para {new_quantity} unidades")
            return True
        else:
            logger.error(f"Erro ao atualizar inventário: {inventory_response.status_code} - {inventory_response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao atualizar inventário: {str(e)}")
        return False

def sync_stock():
    """
    Função principal que sincroniza o stock entre Suprides e Shopify.
    """
    logger.info("Iniciando sincronização de stock")
    
    # Verificar se as credenciais estão configuradas
    if not all([SUPRIDES_USER, SUPRIDES_PASSWORD, SHOPIFY_STORE, SHOPIFY_API_KEY, SHOPIFY_API_PASSWORD]):
        logger.error("Credenciais não configuradas. Verifique as variáveis de ambiente.")
        return
    
    # Obter produtos da Shopify
    shopify_products = get_shopify_products()
    if not shopify_products:
        logger.error("Não foi possível obter produtos da Shopify. Encerrando sincronização.")
        return
    
    # Inicializar contadores para o relatório
    total_products = 0
    updated_products = 0
    failed_updates = 0
    
    # Obter produtos da Suprides (paginação)
    page = 1
    limit = 100
    
    while True:
        suprides_products = get_suprides_products(page, limit)
        
        if not suprides_products:
            logger.error(f"Não foi possível obter produtos da Suprides na página {page}. Encerrando sincronização.")
            break
        
        if len(suprides_products) == 0:
            logger.info(f"Não há mais produtos na página {page}. Finalizando paginação.")
            break
        
        # Processar cada produto da Suprides
        for suprides_product in suprides_products:
            total_products += 1
            
            # Obter o código EAN do produto
            ean = suprides_product.get('ean', '')
            if not ean:
                logger.warning(f"Produto Suprides sem EAN: {suprides_product.get('sku', 'Desconhecido')}. Pulando.")
                continue
            
            # Obter o status de stock do produto
            stock_text = suprides_product.get('stock', '')
            stock_quantity = parse_stock_status(stock_text)
            
            # Encontrar o produto correspondente na Shopify
            shopify_match = find_shopify_product_by_ean(shopify_products, ean)
            
            if shopify_match:
                variant = shopify_match['variant']
                variant_id = variant['id']
                inventory_item_id = variant['inventory_item_id']
                current_quantity = variant.get('inventory_quantity', 0)
                
                # Verificar se é necessário atualizar o stock
                if current_quantity != stock_quantity:
                    logger.info(f"Atualizando stock do produto EAN {ean}: {current_quantity} -> {stock_quantity}")
                    
                    # Atualizar o inventário na Shopify
                    if update_shopify_inventory(variant_id, inventory_item_id, stock_quantity):
                        updated_products += 1
                    else:
                        failed_updates += 1
                else:
                    logger.info(f"Stock já atualizado para o produto EAN {ean}: {current_quantity}")
            else:
                logger.warning(f"Produto com EAN {ean} não encontrado na Shopify. Pulando.")
        
        # Avançar para a próxima página
        page += 1
    
    # Gerar relatório de sincronização
    logger.info("=== Relatório de Sincronização ===")
    logger.info(f"Total de produtos processados: {total_products}")
    logger.info(f"Produtos atualizados com sucesso: {updated_products}")
    logger.info(f"Falhas na atualização: {failed_updates}")
    logger.info("================================")

if __name__ == "__main__":
    logger.info("=== Iniciando script de sincronização de stock ===")
    logger.info(f"Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        sync_stock()
        logger.info("Sincronização concluída com sucesso")
    except Exception as e:
        logger.error(f"Erro durante a sincronização: {str(e)}")
    
    logger.info("=== Fim do script de sincronização de stock ===")
