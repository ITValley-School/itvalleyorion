from itvalleyorion import Operator, Analyst, Supervisor, tool, OrionServices, set_default_orion_key
from pydantic import BaseModel, Field
from typing import List, Dict
import asyncio


class AnaliseMercado(BaseModel):
    tendencia: str = Field(description="Tendência geral do mercado (alta, baixa, estável)")
    confianca: float = Field(description="Nível de confiança na análise (0-1)")
    acoes_recomendadas: List[str] = Field(description="Lista de ações recomendadas")



# Definir ferramentas com o decorador @tool
@tool
def buscar_cotacao(ticker: str) -> Dict[str, float]:
    """Busca a cotação atual e histórica de uma ação pelo seu ticker."""
    # Implementação fictícia
    return {
        "atual": 45.70,
        "abertura": 44.80,
        "maxima": 46.20,
        "minima": 44.30,
        "volume": 1250000
    }

@tool
def dados_economicos(pais: str) -> Dict[str, float]:
    """Obtém indicadores econômicos de um país."""
    # Implementação fictícia
    return {
        "inflacao": 4.2,
        "pib_crescimento": 2.1,
        "desemprego": 7.8,
        "juros": 5.5
    }


redatorSimples = Operator(
    name="Redator Simples",
    instructions="Escreva um texto simples sobre o mercado financeiro."
)    


analystData = Analyst(
    name="Analista de Dados",
    instructions="Analise os dados e forneça insights detalhados.",
    tools=[buscar_cotacao, dados_economicos],
    output_type=AnaliseMercado,
    require_output_type=True
)

# Criar o supervisor
supervidorGeral = Supervisor(
    name="Coordenador de Análise",
    instructions="""Você é um coordenador de análise financeira.
    
    Sua função é entender a solicitação do usuário e decidir qual é a melhor abordagem:
    1. Se o usuário quer apenas uma descrição simples do mercado, delegue para o Redator Simples.
    2. Se o usuário quer uma análise técnica detalhada, delegue para o Analista de Dados.
    
    Antes de delegar, certifique-se de entender exatamente o que o usuário precisa.
    """,
    supervised_agents=[redatorSimples, analystData]
)

async def main():
    # Teste 1: Solicitação simples
    print("=== SOLICITAÇÃO SIMPLES ===")
    resultado1 = await supervidorGeral.run(
        "Preciso de um resumo breve sobre o mercado de ações brasileiro hoje."
    )
    print(resultado1)
    
    print("\n=== SOLICITAÇÃO TÉCNICA ===")
    resultado2 = await supervidorGeral.run(
        "Preciso de uma análise técnica detalhada do setor bancário, especialmente sobre as ações do Itaú."
    )
    print(resultado2)

if __name__ == "__main__":
    asyncio.run(main())
