import json
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable, Type, get_type_hints
from pydantic import BaseModel

from ..auth import get_orion_key
from .operatorsdk import Operator, AgentResult
from .analystsdk import Analyst, tool
import requests

class Supervisor:
    """
    Agente supervisor que coordena e delega tarefas entre múltiplos agentes.
    
    O Supervisor é capaz de analisar uma tarefa, decidir qual agente é mais adequado
    para executá-la, e coordenar o fluxo de trabalho entre diferentes agentes.
    
    Exemplo de uso:
    ```python
    from itvalleyorion import Operator, Analyst, Supervisor, tool, set_default_orion_key
    from pydantic import BaseModel, Field
    
    # Configurar autenticação
    set_default_orion_key("sua-chave-api-orion")
    
    # Criar agentes supervisionados
    redator = Operator(
        name="Redator de Conteúdo",
        instructions="Crie conteúdo sobre o tema solicitado."
    )
    
    analista = Analyst(
        name="Analista de Dados",
        instructions="Analise os dados fornecidos.",
        tools=[buscar_dados]  # função decorada com @tool
    )
    
    # Criar supervisor
    coordenador = Supervisor(
        name="Coordenador de Projetos",
        instructions="Coordene a criação de relatórios financeiros.",
        supervised_agents=[redator, analista],
        tools=[verificar_disponibilidade]  # função decorada com @tool
    )
    
    # Executar supervisor
    resultado = await coordenador.run("Precisamos de um relatório sobre o mercado de ações.")
    print(resultado)
    ```
    """
    
    def __init__(self, name: str, instructions: str, 
                supervised_agents: List[Union[Operator, Analyst]] = None,
                output_type: Type[BaseModel] = None,
                tools: List[Callable] = None,
                require_output_type: bool = False):
        """
        Inicializa um agente Supervisor.
        
        Args:
            name (str): Nome do supervisor
            instructions (str): Instruções detalhadas para o supervisor
            supervised_agents (List[Union[Operator, Analyst]], optional): Lista de agentes supervisionados
            output_type (Type[BaseModel], optional): Modelo Pydantic para estruturar a saída
            tools (List[Callable], optional): Lista de funções decoradas com @tool
            require_output_type (bool, optional): Se True, lança erro se output_type não for fornecido
        """
        self.name = name
        self.instructions = instructions
        self.supervised_agents = supervised_agents or []
        self.output_type = output_type
        self.require_output_type = require_output_type
        self.base_url = "https://app-orion-dev.azurewebsites.net"
        
        # Verificar se output_type é obrigatório
        if self.require_output_type and not self.output_type:
            raise ValueError("output_type é obrigatório quando require_output_type=True")
        
        # Processar ferramentas (mesmo sistema do Analyst)
        self.tools = []
        if tools:
            # Obter as ferramentas registradas (do módulo analystsdk)
            from .analystsdk import _REGISTERED_TOOLS
            
            for tool_func in tools:
                tool_name = tool_func.__name__
                if tool_name in _REGISTERED_TOOLS:
                    self.tools.append(_REGISTERED_TOOLS[tool_name])
                else:
                    # Se a função não foi decorada, tenta registrá-la automaticamente
                    decorated = tool(tool_func)
                    if decorated.__name__ in _REGISTERED_TOOLS:
                        self.tools.append(_REGISTERED_TOOLS[decorated.__name__])
    
    def add_supervised_agent(self, agent: Union[Operator, Analyst]):
        """
        Adiciona um agente à lista de supervisionados.
        
        Args:
            agent (Union[Operator, Analyst]): Agente a ser supervisionado
            
        Returns:
            Supervisor: Self para chamadas encadeadas
        """
        self.supervised_agents.append(agent)
        return self
    
    async def run(self, input_text: str) -> Union[AgentResult, BaseModel]:
        """
        Executa o supervisor com o texto de entrada fornecido.
        
        O supervisor analisará o input, decidirá qual agente deve lidar com a tarefa,
        e poderá executar ferramentas ou delegar para outros agentes conforme necessário.
        
        Args:
            input_text (str): Texto de entrada para o supervisor processar
            
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
        
        # Preparar informações das ferramentas (mesmo sistema do Analyst)
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
        
        # Preparar informações dos agentes supervisionados
        supervised_agents_info = []
        for agent in self.supervised_agents:
            agent_type = "operator" if isinstance(agent, Operator) else "analyst"
            
            # Extrair informações do agente
            agent_info = {
                "id": id(agent),  # Usar ID único para referência
                "name": agent.name,
                "type": agent_type,
                "instructions": agent.instructions
            }
            
            # Adicionar informações específicas para analistas
            if agent_type == "analyst" and hasattr(agent, 'tools') and agent.tools:
                agent_tools = []
                for tool_data in agent.tools:
                    agent_tools.append({
                        "name": tool_data["name"],
                        "description": tool_data["description"]
                    })
                agent_info["tools"] = agent_tools
            
            supervised_agents_info.append(agent_info)
        
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
        response = await self._call_orion_api(full_prompt, tools_info, supervised_agents_info, output_schema)
        
        # Processar o resultado
        result = AgentResult(response.get("content", ""), raw_response=response)
        
        # Se tipo de saída foi especificado, converter para estrutura
        if self.output_type:
            try:
                # Reutilizar o parser do Analyst
                from .analystsdk import Analyst
                analyst_instance = Analyst("temp", "temp", output_type=self.output_type)
                return analyst_instance._parse_output_to_model(result.content, self.output_type)
            except Exception as e:
                if self.require_output_type:
                    raise ValueError(f"Não foi possível converter o resultado para {self.output_type.__name__}: {str(e)}")
                return result
        
        return result
    
    async def _call_orion_api(self, prompt: str, tools: List[Dict], 
                      supervised_agents: List[Dict], output_schema: Dict = None) -> Dict[str, Any]:
        """Chama a API do Orion com informações avançadas e gerencia delegação para outros agentes"""
        api_key = get_orion_key()
        
        endpoint = f"{self.base_url}/api/agents/run"
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1500,
            "agent_type": "supervisor",
            "tools": tools,
            "supervised_agents": supervised_agents
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
        
        result = response.json()
        
        # Verificar se há chamadas de ferramentas ou delegação para agentes
        needs_more_processing = True
        max_iterations = 10  # Limite de iterações para evitar loops infinitos
        current_iteration = 0
        
        while needs_more_processing and current_iteration < max_iterations:
            current_iteration += 1
            needs_more_processing = False
            
            # Processar chamadas de ferramentas
            if "tool_calls" in result:
                needs_more_processing = True
                
                # Executar as ferramentas e coletar resultados
                tool_results = []
                for tool_call in result["tool_calls"]:
                    tool_result = self._execute_tool_call(tool_call)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "result": tool_result
                    })
                
                # Enviar resultados de volta para o modelo
                payload["tool_results"] = tool_results
                response = requests.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            # Processar delegações para agentes supervisionados
            if "agent_delegations" in result:
                needs_more_processing = True
                
                # Executar cada delegação e coletar resultados
                delegation_results = []
                for delegation in result["agent_delegations"]:
                    delegation_result = await self._execute_agent_delegation(delegation)
                    delegation_results.append({
                        "delegation_id": delegation["id"],
                        "result": delegation_result
                    })
                
                # Enviar resultados de volta para o modelo
                payload["delegation_results"] = delegation_results
                response = requests.post(endpoint, json=payload, headers=headers)
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
    
    async def _execute_agent_delegation(self, delegation: Dict[str, Any]) -> str:
        """Executa uma delegação para um agente supervisionado e retorna o resultado"""
        agent_id = delegation.get("agent_id")
        input_for_agent = delegation.get("input", "")
        
        # Encontrar o agente pelo ID
        agent = None
        for a in self.supervised_agents:
            if id(a) == agent_id:
                agent = a
                break
        
        if not agent:
            return f"Erro: Agente com ID {agent_id} não encontrado"
        
        try:
            # Executar o agente com o input fornecido
            result = await agent.run(input_for_agent)
            
            # Converter o resultado para string
            if isinstance(result, AgentResult):
                return result.content
            elif isinstance(result, BaseModel):
                return json.dumps(result.dict())
            else:
                return str(result)
        except Exception as e:
            return f"Erro ao executar o agente {agent.name}: {str(e)}"