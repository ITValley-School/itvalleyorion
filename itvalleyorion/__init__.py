from .orionsdk import OrionServices

# Exportar a função de autenticação
from .auth import set_default_orion_key

# Exportar as classes de agentes
from .agents.operatorsdk import Operator, AgentResult
from .agents.analystsdk import Analyst, AgentResult
from .agents.supervisorsdk import Supervisor

# Definir o que é exposto ao importar *
__all__ = [
    'Operator',
    'Analyst',
    'AgentResult',
    'set_default_orion_key',
    'tool'
]

