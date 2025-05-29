import requests

def send_discord_message(webhook_url, message):
    data = {
        "content": message
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Falha ao enviar mensagem: {response.status_code}, {response.text}")
