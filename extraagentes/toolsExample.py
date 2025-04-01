from pydantic import BaseModel, Field

# Definir um modelo Pydantic para a ferramenta
class DataAnalysisReport(BaseModel):
    summary: str = Field(description="Resumo geral da análise de dados.")
    insights: list[str] = Field(description="Lista de insights obtidos a partir dos dados.")
    recommendations: list[str] = Field(description="Recomendações baseadas na análise.")
    confidence_score: float = Field(
        description="Pontuação de confiança na análise, variando de 0.0 a 1.0."
    )

# Função para gerar a definição da ferramenta
def generate_tool(schema: Type[BaseModel], description: str) -> Dict[str, Any]:
    """
    Gera uma definição de ferramenta (tool) com base em um modelo Pydantic.

    Args:
        schema (Type[BaseModel]): A classe Pydantic que define a estrutura da saída.
        description (str): Uma descrição personalizada da ferramenta para o usuário.

    Returns:
        Dict[str, Any]: Um dicionário contendo a definição da ferramenta.
    """
    schema_json = schema.model_json_schema()
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

# Gerar a definição da ferramenta
tool = generate_tool(
    DataAnalysisReport,
    "Gera um relatório estruturado de análise de dados, incluindo resumo, insights, recomendações e pontuação de confiança."
)

# Exibir a definição da ferramenta
print(tool)
"""
Saida Exemplo:
{
    "name": "DataAnalysisReport",
    "description": "Gera um relatório estruturado de análise de dados, incluindo resumo, insights, recomendações e pontuação de confiança.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "title": "Summary",
                "type": "string",
                "description": "Resumo geral da análise de dados."
            },
            "insights": {
                "title": "Insights",
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Lista de insights obtidos a partir dos dados."
            },
            "recommendations": {
                "title": "Recommendations",
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Recomendações baseadas na análise."
            },
            "confidence_score": {
                "title": "Confidence Score",
                "type": "number",
                "description": "Pontuação de confiança na análise, variando de 0.0 a 1.0."
            }
        },
        "required": ["summary", "insights", "recommendations", "confidence_score"]
    }
}

"""