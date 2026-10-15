# PIM IV - Sistema de Gestão

Este projeto é um sistema de gestão desenvolvido como parte do Projeto Integrado Multidisciplinar (PIM IV) do curso de Análise e Desenvolvimento de Sistemas.

## Configuração Automática

Este projeto possui um mecanismo de auto-instalação para facilitar o início do desenvolvimento:

1. Localize o arquivo `iniciar_sistema.bat` na raiz do projeto.
2. Execute o arquivo com um duplo clique.
3. O script irá configurar automaticamente o ambiente, instalar as dependências necessárias e preparar a estrutura para execução.

## Estrutura do Projeto

- **/backend**: API desenvolvida em Python (FastAPI).
- **/frontend**: Interface web (PWA) com HTML, CSS e JavaScript.
- **/database**: Scripts SQL para migração e inicialização do banco de dados.

## Como utilizar

- **Execução**: Após a configuração automática, o sistema estará pronto para rodar. Utilize o arquivo `.bat` fornecido para garantir que o ambiente esteja ativado corretamente.
- **Documentação**: Detalhes sobre os requisitos acadêmicos e as especificações técnicas do PIM IV podem ser consultados no arquivo `Manual_PIM_IV - ADS - Versão 2.docx` ou no `manual_pim_iv.txt` localizados na raiz do repositório.
- **Desenvolvimento**: Siga a estrutura de pastas existente. O backend contém testes automatizados (`test_*.py`) para garantir a integridade da API e das migrações do banco.
