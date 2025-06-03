import os

print("🔍 Variáveis de ambiente disponíveis no GitHub Actions:\n")
for key in sorted(os.environ):
    if "SUPRIDES" in key or "SHOPIFY" in key:
        print(f"{key} = {os.getenv(key)}")
