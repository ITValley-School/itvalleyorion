import requests
from typing import Dict, Any

from ..auth import get_orion_key

class AgentResult:
    """Classe para representar o resultado de uma execução de agente"""
    
    def __init__(self, content: str, raw_response: Dict[str, Any] = None):
        self.content = content
        self.raw_response = raw_response or {}
    
    def __str__(self) -> str:
        return self.content


class Operator:
    """
    Agente básico que executa tarefas específicas usando a plataforma Orion.
    
    Exemplo de uso:
    ```python
    from itvalleyorion import Operator, set_default_orion_key
    
    # Configurar autenticação uma única vez
    set_default_orion_key("sua-chave-api-orion")
    
    # Criar um operador
    classificador = Operator(
        name="Classificador de Texto",
        instructions="Classifique o texto como positivo, negativo ou neutro."
    )
    
    # Executar o agente
    result = await classificador.run("Este produto é excelente!")
    print(result)
    ```
    """
    
    def __init__(self, name: str, instructions: str):
        """
        Inicializa um agente Operator.
        
        Args:
            name (str): Nome do agente
            instructions (str): Instruções detalhadas para o agente
        """
        self.name = name
        self.instructions = instructions
        self.base_url = "https://app-orion-dev.azurewebsites.net"
    
    async def run(self, input_text: str) -> AgentResult:
        """
        Executa o agente com o texto de entrada fornecido.
        
        Args:
            input_text (str): Texto de entrada para o agente processar
            
        Returns:
            AgentResult: Resultado da execução do agente
        """
        # Construir o prompt completo com as instruções
        full_prompt = f"""# Instruções para {self.name}
{self.instructions}

# Entrada
{input_text}

# Saída
"""
        
        # Chamar a API do Orion
        response = self._call_orion_api(full_prompt)
        return AgentResult(response.get("content", ""), raw_response=response)
    
    def _call_orion_api(self, prompt: str) -> Dict[str, Any]:
        """Chama a API do Orion para processar o prompt"""
        # Obter a chave da API do módulo de autenticação
        api_key = get_orion_key()
        
        endpoint = f"{self.base_url}/api/agents/run"
        
        payload = {
            "prompt": prompt,
            # Outros parâmetros são gerenciados pelo backend do Orion
            "max_tokens": 1000
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()