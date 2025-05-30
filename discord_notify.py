import requests

def send_discord_message(webhook_url, message):
    payload = {"content": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 204:
        print("✅ Mensagem enviada para o Discord!")
    else:
        print(f"❌ Erro ao enviar mensagem Discord: {response.status_code}")
