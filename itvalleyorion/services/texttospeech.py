import requests
import os
from typing import Dict, Optional, BinaryIO, Union, Any

class TextToSpeechService:
    """
    Serviço para conversão de texto em áudio utilizando o Orion API.
    
    Este serviço permite converter textos em arquivos de áudio usando
    o modelo Text-to-Speech da OpenAI através da API do Orion.
    """
    
    def __init__(self, api_key: str, base_url: str):
        """
        Inicializa o serviço de conversão de texto em áudio.
        
        Args:
            api_key (str): Chave de API para autenticação.
            base_url (str): URL base da API do Orion.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.endpoint = f"{self.base_url}/api/openai/tts"
    
    def text_to_speech(self, text: str, output_file: str = None, voice: str = "alloy") -> bytes:
        """
        Converte texto em áudio.
        
        Args:
            text (str): Texto a ser convertido em áudio.
            output_file (str, optional): Caminho para o arquivo onde o áudio será salvo.
                Se não for fornecido, o áudio será retornado como bytes.
            voice (str, optional): Voz a ser utilizada. Padrão é "alloy".
                Opções possíveis incluem: "alloy", "echo", "fable", "onyx", "nova", "shimmer".
            
        Returns:
            bytes: Dados do áudio em formato binário, se output_file não for especificado.
                  Caso contrário, retorna None após salvar o arquivo.
            
        Raises:
            requests.HTTPError: Se houver um erro na chamada da API.
            IOError: Se houver um erro ao salvar o arquivo.
        """
        # Preparar os dados para a requisição
        data = {
            "text": text,
            "voice": voice
        }
        
        # Configurar cabeçalhos
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Fazer a requisição
        response = requests.post(
            self.endpoint,
            headers=headers,
            data=data
        )
        
        # Verificar se houve erro na requisição
        response.raise_for_status()
        
        # Obter o conteúdo binário do áudio
        audio_content = response.content
        
        # Se output_file for especificado, salvar o áudio em arquivo
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(audio_content)
            return None
        
        # Caso contrário, retornar o conteúdo binário
        return audio_content
    
    def text_to_speech_batch(self, texts: Dict[str, str], output_dir: str, voice: str = "alloy") -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Converte múltiplos textos em áudios, salvando-os em arquivos.
        
        Args:
            texts (Dict[str, str]): Dicionário com nome_do_arquivo -> texto para conversão.
            output_dir (str): Diretório onde os arquivos de áudio serão salvos.
            voice (str, optional): Voz a ser utilizada. Padrão é "alloy".
                
        Returns:
            Dict[str, Union[str, Dict[str, str]]]: Dicionário com resultados e erros.
                Por exemplo:
                {
                    "results": {"arquivo1.mp3": "Caminho completo para o arquivo"},
                    "errors": {"arquivo2.mp3": "Mensagem de erro"}
                }
                
        Raises:
            ValueError: Se o diretório de saída não existir.
        """
        # Verificar se o diretório de saída existe
        if not os.path.exists(output_dir):
            raise ValueError(f"Diretório de saída não encontrado: {output_dir}")
        
        results = {}
        errors = {}
        
        # Processar cada texto
        for filename, text in texts.items():
            try:
                # Garantir que o nome do arquivo tenha a extensão .mp3
                if not filename.lower().endswith('.mp3'):
                    filename = f"{filename}.mp3"
                
                # Caminho completo para o arquivo de saída
                output_path = os.path.join(output_dir, filename)
                
                # Converter o texto em áudio e salvar o arquivo
                self.text_to_speech(text, output_path, voice)
                
                # Registrar o resultado
                results[filename] = output_path
            except Exception as e:
                # Registrar o erro
                errors[filename] = str(e)
        
        # Retornar os resultados e erros
        return {
            "results": results,
            "errors": errors
        }