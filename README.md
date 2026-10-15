# PIM IV - Sistema de Gestão

Este projeto é um sistema de gestão desenvolvido como parte do Projeto Integrado Multidisciplinar (PIM IV) do curso de Análise e Desenvolvimento de Sistemas.

## ⚙️ Configuração Automática

Este projeto possui um mecanismo de **auto-instalação e auto-configuração**:

1. Localize o arquivo `iniciar_sistema.bat` na raiz do projeto.
2. Execute o arquivo com um duplo clique.
3. O script irá configurar automaticamente o ambiente virtual, instalar as dependências (`requirements.txt`), verificar o banco de dados e preparar a estrutura para execução.

## 📂 Estrutura do Projeto

```text
.
├── backend
│   ├── app/            # Código fonte da API (FastAPI)
│   ├── .env            # Variáveis de ambiente
│   ├── requirements.txt# Dependências do backend
│   └── test_*.py       # Suíte de testes automatizados
├── database
│   ├── init.sql        # Script de inicialização
│   └── migrations_*.sql# Scripts de migração por módulo
├── frontend
│   ├── icons/          # Recursos visuais e ícones PWA
│   ├── app.js          # Lógica da interface e suporte a PWA
│   ├── manifest.json   # Configuração da Web App (PWA)
│   ├── style.css       # Estilização da interface
│   └── sw.js           # Service Worker para suporte offline
├── iniciar_sistema.bat # Script de auto-instalação
└── ...
```

## 📦 Dependências

O backend utiliza **Python 3.x** e as seguintes bibliotecas principais (instaladas automaticamente via `requirements.txt`):
- `fastapi`: Framework web de alta performance.
- `uvicorn`: Servidor ASGI para rodar a aplicação.
- `sqlalchemy`: ORM para integração com banco de dados.
- `pytest`: Framework de testes automatizados.

## 🚀 Como utilizar

- **Execução**: Execute o `iniciar_sistema.bat` sempre que iniciar o ambiente de desenvolvimento. Ele cuidará de subir os serviços necessários.
- **PWA (App Móvel)**: O sistema suporta instalação como aplicativo móvel (PWA). Acesse o sistema via navegador e clique no botão **"Instalar App"** na barra superior para adicionar o atalho à tela inicial do seu dispositivo.
- **Documentação**: Detalhes sobre requisitos acadêmicos podem ser consultados no arquivo `Manual_PIM_IV - ADS - Versão 2.docx` ou no `manual_pim_iv.txt`.
- **Testes**: Utilize os arquivos `test_api.py`, `test_database_schema.py` e `test_full_suite.py` dentro da pasta `backend` para validar as alterações.

---

## 📋 Histórico de Atualizações

### 🔄 Atualização (15/10/2026)
- Implementação completa de suporte a PWA (Progressive Web App): adição de `manifest.json`, `sw.js` (Service Worker) e lógica de `beforeinstallprompt` no `app.js`.
- Inclusão do botão de instalação de aplicativo no header e atualização dos ícones oficiais da marca na pasta `/frontend/icons`.
- Atualização estrutural do README para refletir as novas capacidades de instalação e a nova organização de assets visuais.

- Inclusão da estrutura inicial do projeto com separação clara entre `backend`, `frontend` e `database`.
- Criação do script `iniciar_sistema.bat` para automatização do ambiente.
- Adição de documentação básica de uso e estrutura.
