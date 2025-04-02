import os
from typing import Dict, Optional, BinaryIO, Union, Any

from services.transcriptionaudio import TranscriptionAudioService
from services.texttospeech import TextToSpeechService


class Orion:
    """
    SDK unificado para acessar os serviços de IA do Orion.
    
    Este SDK fornece acesso a todos os serviços disponíveis na API do Orion,
    incluindo transcrição de áudio, conversão de texto em áudio, e mais.
    
    Exemplo de uso:
    ```python
    # Inicializar o SDK
    cliente = Orion("sua-api-key")
    
    # Usar o serviço de transcrição de áudio
    resultado = cliente.audio.transcribe_file("audio.mp3")
    
    # Usar o serviço de texto para áudio
    cliente.tts.text_to_speech("Olá, mundo!", "saida.mp3")
    ```
    """
    
    def __init__(self, api_key: str = None, base_url: str = "https://app-orion-dev.azurewebsites.net"):
        """
        Inicializa o SDK do Orion.
        
        Args:
            api_key (str, optional): Chave de API para autenticação. 
                Se não for fornecida, tentará buscar da variável de ambiente ORION_API_KEY.
            base_url (str, optional): URL base da API do Orion.
                Padrão é "https://app-orion-dev.azurewebsites.net".
        """
        self.api_key = api_key or os.environ.get("ORION_API_KEY")
        if not self.api_key:
            raise ValueError("API key não fornecida. Defina a variável ORION_API_KEY ou passe a chave no construtor.")
        
        self.base_url = base_url
        
        # Inicializar os serviços
        self.audio = TranscriptionAudioService(self.api_key, self.base_url)
        self.tts = TextToSpeechService(self.api_key, self.base_url)

        


# Exemplo de uso
if __name__ == "__main__":
    # Configuração do SDK
    api_key = "sua_chave_api_aqui"  # Substitua pela sua chave API
    cliente = Orion(api_key)
    
    # Exemplo de transcrição de áudio
    try:
        print("=== EXEMPLO DE TRANSCRIÇÃO DE ÁUDIO ===")
        resultado = cliente.audio.transcribe_file("sample.mp3")
        print(f"Transcrição: {resultado['transcription'][:100]}...")
    except Exception as e:
        print(f"Erro na transcrição: {e}")
    
    # Exemplo de conversão de texto em áudio
    try:
        print("\n=== EXEMPLO DE CONVERSÃO DE TEXTO EM ÁUDIO ===")
        texto = "Olá, esta é uma demonstração do serviço de conversão de texto em áudio."
        cliente.tts.text_to_speech(texto, "exemplo_tts.mp3")
        print("Áudio gerado com sucesso!")
    except Exception as e:
        print(f"Erro na conversão de texto em áudio: {e}")