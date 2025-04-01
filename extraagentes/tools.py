from typing import Type, Dict, Any
from pydantic import BaseModel

def generate_tool_outputstructure(schema: Type[BaseModel], description: str) -> Dict[str, Any]:
    """
    Gera uma definição de ferramenta (tool) com base em um modelo Pydantic.

    Essa função é genérica e pode ser usada em diferentes sistemas que aceitam
    definições de ferramentas, como OpenAI, DeepSeek, etc.

    Args:
        schema (Type[BaseModel]): A classe Pydantic que define a estrutura da saída.
        description (str): Uma descrição personalizada da ferramenta para o usuário.

    Returns:
        Dict[str, Any]: Um dicionário contendo a definição da ferramenta.
    """
    # Obter a definição do schema para a API de funções
    schema_json = schema.model_json_schema()

    # Criar a definição da ferramenta
    tool_definition = {
        "name": schema.__name__,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": schema_json.get("properties", {}),
            "required": schema_json.get("required", [])
        }
    }

    return tool_definition