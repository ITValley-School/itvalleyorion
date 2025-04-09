"""
Módulo de autenticação para o SDK de Agentes.

Este módulo gerencia a autenticação com o serviço Orion, fornecendo
funções para definir e obter a chave de API.
"""

import os

# Variável global para armazenar a chave da API
_ORION_API_KEY = None

def set_default_orion_key(api_key: str) -> None:
    """
    Define a chave de API do Orion para ser usada por todos os agentes.
    
    Esta função deve ser chamada antes de utilizar qualquer agente do SDK.
    A chave é armazenada tanto na memória quanto como variável de ambiente.
    
    Args:
        api_key (str): Chave de API para autenticação com o serviço Orion
    
    Exemplo:
    ```python
    from itvalleyorion.agents import set_default_orion_key
    
    # Configurar autenticação uma única vez
    set_default_orion_key("sua-chave-api-orion")
    ```
    """
    global _ORION_API_KEY
    _ORION_API_KEY = api_key
    os.environ["ORION_API_KEY"] = api_key

def get_orion_key() -> str:
    """
    Recupera a chave de API do Orion configurada globalmente.
    
    Tenta obter a chave na seguinte ordem:
    1. Da variável global _ORION_API_KEY
    2. Da variável de ambiente ORION_API_KEY
    
    Returns:
        str: A chave de API do Orion
        
    Raises:
        ValueError: Se nenhuma chave de API foi configurada
    """
    key = _ORION_API_KEY or os.environ.get("ORION_API_KEY")
    if not key:
        raise ValueError(
            "Chave da API Orion não configurada. Use set_default_orion_key() "
            "antes de utilizar os agentes, ou defina a variável de ambiente ORION_API_KEY."
        )
    return key