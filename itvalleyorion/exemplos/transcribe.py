from itvalleyorion.orionsdk import Orion
import requests


client = Orion(api_key="sua_chave_api_aqui")  # Substitua pela sua chave API


# Exemplo de transcrição de áudio

request = client.audio.transcribe_url("https://example.com/sample-audio.mp3")
print("=== TRANSCRIÇÃO DE ÁUDIO POR URL ===")
print(request["transcription"])


