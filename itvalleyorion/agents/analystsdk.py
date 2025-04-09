import inspect
import json
from typing import Dict, Any, Optional, List, Union, Callable, Type, get_type_hints
from pydantic import BaseModel, create_model

from ..auth import get_orion_key
from .operatorsdk import AgentResult
import requests

# Registro de ferramentas disponíveis
_REGISTERED_TOOLS = {}

def tool(func: Callable = None, *, name: str = None, description: str = None):
    """
    Decorador para registrar uma função como ferramenta para o Analyst.
    
    Args:
        func (Callable, optional): A função a ser decorada
        name (str, optional): Nome personalizado para a ferramenta
        description (str, optional): Descrição da ferramenta
        
    Returns:
        Callable: A função decorada
        
    Exemplo:
    ```python
    @tool
    def buscar_preço(produto: str) -> float:
      
    #Busca o preço atual de um produto no banco de dados.
    
        # Implementação
        return 29.99
    ```
    """
    def decorator(func):
        # Extrair informações da função
        func_name = name or func.__name__
        func_description = description or (func.__doc__ or "").strip()
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Extrair parâmetros e seus tipos
        parameters = {}
        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name, str)
            parameters[param_name] = (param_type, ...)
        
        # Criar modelo Pydantic para os parâmetros
        param_model = create_model(f"{func_name}_params", **parameters)
        
        # Registrar a ferramenta
        _REGISTERED_TOOLS[func_name] = {
            "function": func,
            "name": func_name,
            "description": func_description,
            "parameters": param_model,
            "return_type": type_hints.get("return")
        }
        
        return func
    
    # Permitir usar como @tool ou @tool()
    if func is None:
        return decorator
    return decorator(func)


class Analyst:
    """
    Agente analítico avançado que pode executar ferramentas e retornar dados estruturados.
    
    O Analyst é projetado para analisar dados, tomar decisões e executar ações
    através de ferramentas registradas. Pode retornar dados em formatos estruturados
    usando modelos Pydantic.
    
    Exemplo de uso:
    ```python
    from itvalleyorion import Analyst, tool, set_default_orion_key
    from pydantic import BaseModel, Field
    
    # Configurar autenticação
    set_default_orion_key("sua-chave-api-orion")
    
    # Definir modelo de saída
    class AnaliseCliente(BaseModel):
        segmento: str = Field(description="Segmento do cliente (premium, regular, básico)")
        risco: float = Field(description="Nível de risco de 0 a 1")
        recomendações: List[str] = Field(description="Lista de recomendações")
    
    # Definir ferramentas
    @tool
    def buscar_histórico_compras(cliente_id: str) -> List[Dict]:
        '''Busca o histórico de compras do cliente no banco de dados.'''
        # Implementação fictícia
        return [{"data": "2023-01-15", "valor": 250.00, "produto": "Smartphone"}]
    
    # Criar analista
    analista = Analyst(
        name="Analista de Clientes",
        instructions="Analise os dados do cliente e classifique-o em um segmento.",
        output_type=AnaliseCliente,
        tools=[buscar_histórico_compras]
    )
    
    # Usar o analista
    resultado = await analista.run("Analisar cliente ID: 12345")
    print(f"Segmento: {resultado.segmento}")
    print(f"Risco: {resultado.risco}")
    print(f"Recomendações: {resultado.recomendações}")
    ```
    """
    
    def __init__(self, name: str, instructions: str, 
                 output_type: Type[BaseModel] = None,
                 tools: List[Callable] = None,
                 require_output_type: bool = False):
        """
        Inicializa um agente Analyst.
        
        Args:
            name (str): Nome do agente
            instructions (str): Instruções detalhadas para o agente
            output_type (Type[BaseModel], optional): Modelo Pydantic para estruturar a saída
            tools (List[Callable], optional): Lista de funções decoradas com @tool
            require_output_type (bool, optional): Se True, lança erro se output_type não for fornecido
        """
        self.name = name
        self.instructions = instructions
        self.output_type = output_type
        self.require_output_type = require_output_type
        self.base_url = "https://app-orion-dev.azurewebsites.net"
        
        # Verificar se output_type é obrigatório
        if self.require_output_type and not self.output_type:
            raise ValueError("output_type é obrigatório quando require_output_type=True")
        
        # Processar ferramentas
        self.tools = []
        if tools:
            for tool_func in tools:
                tool_name = tool_func.__name__
                if tool_name in _REGISTERED_TOOLS:
                    self.tools.append(_REGISTERED_TOOLS[tool_name])
                else:
                    # Se a função não foi decorada, tenta registrá-la automaticamente
                    decorated = tool(tool_func)
                    if decorated.__name__ in _REGISTERED_TOOLS:
                        self.tools.append(_REGISTERED_TOOLS[decorated.__name__])
    
    async def run(self, input_text: str) -> Union[AgentResult, BaseModel]:
        """
        Executa o agente com o texto de entrada fornecido.
        
        O agente analisará o input, poderá executar ferramentas conforme necessário,
        e retornará o resultado como um objeto estruturado (se output_type for especificado)
        ou como um AgentResult.
        
        Args:
            input_text (str): Texto de entrada para o agente processar
            
        Returns:
            Union[AgentResult, BaseModel]: Resultado da execução ou objeto estruturado
            
        Raises:
            ValueError: Se require_output_type=True mas output_type não foi fornecido
            Exception: Se ocorrer um erro durante a chamada à API
        """
        # Construir o prompt
        full_prompt = f"""# Instruções para {self.name}
{self.instructions}

# Entrada
{input_text}

# Saída
"""
        
        # Preparar informações das ferramentas
        tools_info = []
        for tool_data in self.tools:
            # Extrair informações do schema do modelo de parâmetros
            param_model = tool_data["parameters"]
            parameters_schema = {}
            for field_name, field in param_model.__fields__.items():
                parameters_schema[field_name] = {
                    "type": str(field.type_),
                    "description": field.field_info.description or ""
                }
            
            # Adicionar informações da ferramenta
            tools_info.append({
                "name": tool_data["name"],
                "description": tool_data["description"],
                "parameters": parameters_schema
            })
        
        # Preparar informações do output_type
        output_schema = None
        if self.output_type:
            output_schema = {}
            for field_name, field in self.output_type.__fields__.items():
                output_schema[field_name] = {
                    "type": str(field.type_),
                    "description": field.field_info.description or ""
                }
        
        # Chamar a API do Orion
        response = self._call_orion_api(full_prompt, tools_info, output_schema)
        
        # Processar o resultado
        result = AgentResult(response.get("content", ""), raw_response=response)
        
        # Se tipo de saída foi especificado, converter para estrutura
        if self.output_type:
            try:
                # Tenta extrair dados estruturados
                return self._parse_output_to_model(result.content, self.output_type)
            except Exception as e:
                if self.require_output_type:
                    raise ValueError(f"Não foi possível converter o resultado para {self.output_type.__name__}: {str(e)}")
                return result

        return result
    
    def _call_orion_api(self, prompt: str, tools: List[Dict], output_schema: Dict = None) -> Dict[str, Any]:
        """Chama a API do Orion com informações avançadas"""
        api_key = get_orion_key()
        
        endpoint = f"{self.base_url}/api/agents/run"
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1500,
            "agent_type": "analyst",
            "tools": tools
        }
        
        # Adicionar schema de saída se fornecido
        if output_schema:
            payload["output_schema"] = output_schema
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        
        # Se houver chamadas de ferramentas na resposta
        result = response.json()
        
        # Executar ferramentas se necessário
        if "tool_calls" in result:
            for tool_call in result["tool_calls"]:
                # Executar a ferramenta chamada pelo modelo
                result = self._execute_tool_call(tool_call)
                
                # Enviar o resultado da ferramenta de volta para o modelo
                tool_response_payload = {
                    **payload,
                    "tool_results": [{
                        "tool_call_id": tool_call["id"],
                        "result": result
                    }]
                }
                
                # Chamar a API novamente com o resultado da ferramenta
                response = requests.post(endpoint, json=tool_response_payload, headers=headers)
                response.raise_for_status()
                result = response.json()
        
        return result
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        """Executa uma chamada de ferramenta e retorna o resultado"""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        # Encontrar a ferramenta pelo nome
        tool_info = None
        for t in self.tools:
            if t["name"] == tool_name:
                tool_info = t
                break
        
        if not tool_info:
            return {"error": f"Ferramenta '{tool_name}' não encontrada"}
        
        try:
            # Validar os argumentos usando o modelo Pydantic
            param_model = tool_info["parameters"]
            validated_args = param_model(**arguments)
            
            # Extrair argumentos validados
            arg_dict = validated_args.dict()
            
            # Chamar a função da ferramenta com os argumentos
            function = tool_info["function"]
            result = function(**arg_dict)
            
            # Tentar serializar o resultado
            return json.dumps(result)
        except Exception as e:
            return {"error": f"Erro ao executar ferramenta '{tool_name}': {str(e)}"}
    
    def _parse_output_to_model(self, output: str, model_type: Type[BaseModel]) -> BaseModel:
        """
        Converte a saída de texto em um objeto estruturado usando um modelo Pydantic.
        
        Tenta diversas estratégias para extrair os dados:
        1. Tentar parse direto como JSON
        2. Procurar por bloco JSON no texto
        3. Procurar por pares de chave-valor no texto
        
        Args:
            output (str): Texto de saída do modelo
            model_type (Type[BaseModel]): Classe do modelo Pydantic
            
        Returns:
            BaseModel: Instância do modelo com os dados extraídos
        """
        # Estratégia 1: Tentar parse direto como JSON
        try:
            data = json.loads(output)
            return model_type(**data)
        except json.JSONDecodeError:
            pass  # Handle JSON decoding errors gracefully
        except:
            pass
        
        # Estratégia 2: Procurar por bloco JSON no texto
        try:
            # Procurar texto entre chaves
            start_idx = output.find('{')
            end_idx = output.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = output[start_idx:end_idx+1]
                data = json.loads(json_str)
                return model_type(**data)
        except:
            pass
        
        # Estratégia 3: Procurar por pares de chave-valor
        try:
            data = {}
            for field_name in model_type.__fields__:
                # Padrões para buscar valores
                patterns = [
                    f'"{field_name}"\\s*:\\s*(".*?"|\\d+(\\.\\d+)?|\\[.*?\\]|\\{.*?\\}|true|false|null)',
                    f"{field_name}\\s*:\\s*([^,\\n]+)",
                    f"{field_name.title()}\\s*:\\s*([^,\\n]+)"
                ]
                
                # Procurar por cada padrão
                import re
                for pattern in patterns:
                    matches = re.search(pattern, output, re.IGNORECASE)
                    if matches:
                        value_str = matches.group(1).strip()
                        
                        # Tentar converter para o tipo apropriado
                        if value_str.startswith('"') and value_str.endswith('"'):
                            # String
                            data[field_name] = value_str[1:-1]
                        elif value_str.lower() in ('true', 'false'):
                            # Boolean
                            data[field_name] = value_str.lower() == 'true'
                        elif value_str.startswith('[') and value_str.endswith(']'):
                            # Lista
                            try:
                                data[field_name] = json.loads(value_str)
                            except:
                                data[field_name] = value_str.strip('[]').split(',')
                        else:
                            # Número ou outro valor
                            try:
                                if '.' in value_str:
                                    data[field_name] = float(value_str)
                                else:
                                    data[field_name] = int(value_str)
                            except:
                                data[field_name] = value_str
                        
                        break
            
            # Tentar criar objeto com os dados extraídos
            return model_type(**data)
        except Exception as e:
            raise ValueError(f"Não foi possível extrair dados estruturados: {str(e)}")