"""
Roteador legado de compatibilidade para /api/superadmin.
Redireciona e atende requisições mapeando para o Console de Operações.
"""
from app.routers.console import router

# O router é importado e montado sob demanda
