from typing import Type, Any, Optional, Union, Dict, List, Callable
from pydantic import BaseModel
import json
from openai import OpenAI
import functools

def with_structured_output(pydantic_schema: Type[BaseModel]):
    """
    Decorator para adicionar o método with_structured_output à classe OpenAI.
    """
    # Patch na classe OpenAI para adicionar o método with_structured_output
    def _with_structured_output(
        self: OpenAI, 
        schema: Type[BaseModel], 
        *, 
        include_raw: bool = False,
        **kwargs
    ):
        """
        Retorna uma versão do cliente que força a saída estruturada.
        
        Args:
            schema: A classe Pydantic que define a estrutura da saída
            include_raw: Se deve incluir a resposta bruta no resultado
            kwargs: Argumentos adicionais para passar para a chamada da API
            
        Returns:
            Uma função que pode ser chamada com um prompt para obter respostas estruturadas
        """
        # Obter a definição do schema para a API de funções
        schema_json = schema.model_json_schema()
        
        # Criar a definição da função para a API
        function_def = {
            "name": schema.__name__,
            "description": schema_json.get("description", f"Retorna um objeto {schema.__name__}"),
            "parameters": {
                "type": "object",
                "properties": schema_json.get("properties", {}),
                "required": schema_json.get("required", [])
            }
        }
        
        # Função que será retornada para processar prompts
        def _structured_llm_call(prompt: str, **call_kwargs):
            # Mesclar kwargs do decorator com kwargs da chamada
            merged_kwargs = {**kwargs, **call_kwargs}
            model = merged_kwargs.pop("model", "gpt-4") if "model" not in kwargs else kwargs["model"]
            
            # Chamar a API com a definição de função
            response = self.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                functions=[function_def],
                function_call={"name": function_def["name"]},
                **merged_kwargs
            )
            
            # Extrair a chamada de função da resposta
            function_call = response.choices[0].message.function_call
            if function_call and function_call.arguments:
                try:
                    # Analisar os argumentos JSON
                    parsed_args = json.loads(function_call.arguments)
                    # Criar uma instância do modelo Pydantic
                    structured_output = schema.model_validate(parsed_args)
                    
                    # Retornar o resultado estruturado
                    if include_raw:
                        return {"structured": structured_output, "raw": response}
                    return structured_output
                    
                except Exception as e:
                    raise ValueError(f"Erro ao analisar a resposta: {e}")
            else:
                # Se não recebeu uma chamada de função, tenta analisar o texto
                try:
                    content = response.choices[0].message.content
                    # Procurar por JSON no texto
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```|({[\s\S]*})', content or "")
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2)
                        parsed_data = json.loads(json_str)
                        structured_output = schema.model_validate(parsed_data)
                        
                        if include_raw:
                            return {"structured": structured_output, "raw": response}
                        return structured_output
                    else:
                        raise ValueError(f"Não foi possível extrair JSON da resposta: {content}")
                except Exception as e:
                    raise ValueError(f"Erro ao processar a resposta: {e} - Resposta: {response}")
        
        return _structured_llm_call
    
    # Adicionar o método à classe OpenAI
    OpenAI.with_structured_output = _with_structured_output
    
    # Retornar a função que será usada como decorator
    @functools.wraps(pydantic_schema)
    def decorator(obj):
        if isinstance(obj, OpenAI):
            return obj.with_structured_output(pydantic_schema)
        return obj
    
    return decorator


# Adicione o método diretamente à classe OpenAI para permitir o uso sem decorators
def _patch_openai():
    """Adiciona o método with_structured_output à classe OpenAI."""
    if not hasattr(OpenAI, 'with_structured_output'):
        OpenAI.with_structured_output = lambda self, schema, **kwargs: with_structured_output(schema)(self)

# Aplicar o patch ao importar este módulo
_patch_openai()


# Exemplo de uso:
"""
from pydantic import BaseModel, Field
from typing import Optional
from openai import OpenAI

# Definir um modelo Pydantic para a saída
class Joke(BaseModel):
    setup: str = Field(description="O início da piada")
    punchline: str = Field(description="O desfecho da piada")
    rating: Optional[int] = Field(description="Quão engraçada é a piada, de 1 a 10")

# Instanciar o cliente OpenAI
cliente = OpenAI(api_key="sua-chave-aqui")

# Criar um LLM com saída estruturada
structured_llm = cliente.with_structured_output(Joke)

# Invocar o LLM e obter um objeto Joke
resultado = structured_llm("Conte-me uma piada sobre gatos")
print(f"Setup: {resultado.setup}")
print(f"Punchline: {resultado.punchline}")
if resultado.rating:
    print(f"Rating: {resultado.rating}/10")
"""