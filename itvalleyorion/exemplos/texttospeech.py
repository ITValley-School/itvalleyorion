from itvalleyorion.orionsdk import Orion
import requests


client = Orion(api_key="sua_chave_api_aqui")  # Substitua pela sua chave API

response = client.tts.text_to_speech("Olá, mundo!", "output.mp3")
print("=== CONVERSÃO DE TEXTO EM ÁUDIO ===")
print("Áudio salvo como output.mp3")
