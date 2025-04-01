import requests
import os
from typing import Dict, Optional, BinaryIO, Union, Any

class TranscriptionAudioService:
    """
    Serviço para transcrição de áudio utilizando o Orion API.
    
    Este serviço permite transcrever arquivos de áudio em texto usando
    o modelo Whisper através da API do Orion.
    
    Exemplo de retorno:
    {
        "transcription": "Texto transcrito do áudio..."
    }
    """
    
    def __init__(self, api_key: str = None, base_url: str = "https://app-orion-dev.azurewebsites.net"):
        """
        Inicializa o serviço de transcrição de áudio.
        
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
        self.endpoint = f"{self.base_url}/api/openai/whisper"
    
    def transcribe_file(self, file_path: str) -> Dict[str, str]:
        """
        Transcreve um arquivo de áudio do sistema de arquivos.
        
        Args:
            file_path (str): Caminho para o arquivo de áudio a ser transcrito.
            
        Returns:
            Dict[str, str]: Resposta da API contendo a transcrição no formato:
                {"transcription": "texto transcrito..."}
            
        Raises:
            FileNotFoundError: Se o arquivo não existir.
            requests.HTTPError: Se houver um erro na chamada da API.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        # Determina o tipo MIME com base na extensão do arquivo
        file_ext = os.path.splitext(file_path)[1].lower()
        content_type = self._get_content_type(file_ext)
        
        with open(file_path, "rb") as audio_file:
            return self.transcribe(audio_file, os.path.basename(file_path), content_type)
    
    def transcribe(self, audio_file: BinaryIO, filename: str = "audio.mp3", 
                  content_type: str = "audio/mpeg") -> Dict[str, str]:
        """
        Transcreve um arquivo de áudio já aberto.
        
        Args:
            audio_file (BinaryIO): Arquivo de áudio aberto em modo binário.
            filename (str): Nome do arquivo a ser enviado.
            content_type (str): Tipo MIME do arquivo de áudio.
            
        Returns:
            Dict[str, str]: Resposta da API contendo a transcrição no formato:
                {"transcription": "texto transcrito..."}
            
        Raises:
            requests.HTTPError: Se houver um erro na chamada da API.
        """
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {
            "file": (filename, audio_file, content_type)
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            files=files
        )
        
        # Verifica se houve erro na requisição
        response.raise_for_status()
        
        # Retorna o JSON da resposta
        return response.json()

    def transcribe_url(self, audio_url: str) -> Dict[str, str]:
        """
        Transcreve um arquivo de áudio a partir de uma URL.
        
        Args:
            audio_url (str): URL do arquivo de áudio a ser transcrito.
            
        Returns:
            Dict[str, str]: Resposta da API contendo a transcrição no formato:
                {"transcription": "texto transcrito..."}
            
        Raises:
            requests.HTTPError: Se houver um erro ao baixar o arquivo ou na chamada da API.
        """
        # Extrai o nome do arquivo da URL
        filename = os.path.basename(audio_url.split('?')[0])
        
        # Determina o tipo MIME com base na extensão do arquivo
        file_ext = os.path.splitext(filename)[1].lower()
        content_type = self._get_content_type(file_ext)
        
        # Baixa o arquivo de áudio
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        # Envia o conteúdo baixado para transcrição
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {
            "file": (filename, response.content, content_type)
        }
        
        api_response = requests.post(
            self.endpoint,
            headers=headers,
            files=files
        )
        
        # Verifica se houve erro na requisição
        api_response.raise_for_status()
        
        # Retorna o JSON da resposta
        return api_response.json()
    
    def _get_content_type(self, file_ext: str) -> str:
        """
        Determina o tipo MIME apropriado com base na extensão do arquivo.
        
        Args:
            file_ext (str): Extensão do arquivo.
            
        Returns:
            str: Tipo MIME correspondente.
        """
        content_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.wma': 'audio/x-ms-wma'
        }
        
        return content_types.get(file_ext, 'audio/mpeg')  # Padrão para audio/mpeg se desconhecido

# Exemplo de uso
if __name__ == "__main__":
    # Configuração do serviço
    api_key = "sua_chave_api_aqui"  # Substitua pela sua chave API
    transcription_service = TranscriptionAudioService(api_key)
    
    # Exemplo de transcrição de arquivo local
    try:
        result = transcription_service.transcribe_file("sample.mp3")
        print("Transcrição do áudio:")
        print(result["transcription"])
        
        # Exemplo de saída formatada:
        # Transcrição do áudio:
        # "Você ainda está disposto a celebrar? Então deixa eu te dizer algo Quem quer a glória traz a arca, querido..."
    except Exception as e:
        print(f"Erro ao transcrever o áudio: {e}")


