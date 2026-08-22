# Lenos-IA

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-4169E1?style=for-the-badge&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic)](https://pydantic.dev/docs/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)](https://redis.io/docs/latest/integrate/redis-py/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=googlegemini)](https://ai.google.dev/gemini-api/docs?hl=pt-br)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube)](https://developers.google.com/youtube/v3)
[![Resend](https://img.shields.io/badge/Resend-000000?style=for-the-badge&logo=resend)](https://resend.com/docs/send-with-fastapi)

## 📝 Descrição

O **Lenos-IA** é uma plataforma de backend robusta desenvolvida para automatizar a análise de feedback em vídeos do YouTube. Utilizando o poder do **Google Gemini AI**, o sistema extrai e processa comentários para gerar relatórios detalhados sobre o sentimento da audiência, temas recorrentes e métricas comportamentais.

Este projeto foi concebido como um trabalho de graduação (Fatec Franca) e foca em fornecer insights acionáveis para criadores de conteúdo, permitindo uma compreensão profunda da recepção de seus vídeos de forma rápida e precisa.

## ✨ Funcionalidades

*   **Autenticação e autorização** com JWT em cookies HttpOnly.
*   **Integração com OAuth 2.0 do Google** para conectar a conta do usuário.
*   **Validação de propriedade do vídeo**, garantindo que o relatório seja gerado apenas para vídeos do canal autenticado.
*   **Coleta de comentários via YouTube Data API** com paginação e tratamento de erros.
*   **Geração de relatórios com Gemini**, incluindo análise de sentimento, temas, elogios, críticas e recomendações.
*   **Persistência em PostgreSQL** com ORM assíncrono via SQLAlchemy.
*   **Cache em Redis** para acelerar listagens e invalidação após alterações.
*   **Enfileiramento de processamento em background** para geração dos relatórios.
*   **Envio de e-mails transacionais** para verificação de conta e recuperação de senha.
*   **Rate limiting** em rotas sensíveis com SlowAPI.

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| **FastAPI** | Framework Web de alta performance |
| **SQLAlchemy (Async)** | ORM para interação assíncrona com banco de dados |
| **PostgreSQL** | Banco de dados relacional principal |
| **Alembic** | Gerenciamento de migrações de banco de dados |
| **Redis** | Cache |
| **Google Gemini API** | Motor de Inteligência Artificial Generativa |
| **YouTube Data API** | Extração de dados da plataforma YouTube |
| **Argon2** | Hashing de senhas de última geração |
| **Pydantic v2** | Validação de dados e modelagem de schemas |
| **Resend** | Serviço de entrega de e-mails transacionais |
| **HTTPX** | Requisições assíncronas para integrações externas |
| **Google API Python Client** | Integração com serviços do YouTube |
| **Google Auth** | Credenciais OAuth para o fluxo do YouTube |
| **Google GenAI** | Cliente oficial para geração com Gemini |
| **SlowAPI** | Limitação de taxa por endpoint |
| **Pydantic Settings** | Carregamento de variáveis de ambiente |

## 🏗️ Arquitetura do Projeto

O projeto segue uma **arquitetura em camadas** com separação clara de responsabilidades:

1. **`src/api/routes/`**: expõe os endpoints HTTP e define os contratos de resposta.
2. **`src/service/`**: concentra as regras de negócio e a orquestração dos fluxos.
3. **`src/repository/`**: cuida do acesso a dados com SQLAlchemy.
4. **`src/models/`**: define as entidades do banco de dados.
5. **`src/utils/`**: reúne schemas, exceções, autenticação, logging e helpers.
6. **`src/database/`**: centraliza as conexões com PostgreSQL e Redis.
7. **`alembic/`**: contém as migrações de schema do banco.

### Estrutura de Diretórios

```text
/
├── alembic/            # Scripts de migração de banco de dados
├── src/
│   ├── api/routes/      # Endpoints da API
│   ├── app/main.py      # Inicialização do FastAPI e roteamento
│   ├── database/       # Conexões com Postgres e Redis
│   ├── models/         # Modelos ORM do SQLAlchemy
│   ├── repository/     # Camada de persistência de dados
│   ├── service/        # Lógica de negócio e integrações
│   ├── utils/          # Schemas, exceções, logging e helpers
│   └── middlewares/    # Middlewares da aplicação
└── alembic.ini         # Configuração do Alembic
```

## 📡 API Endpoints (Principais)

### Autenticação e conta
*   `POST /v1/user/register`: Registro de novo usuário.
*   `POST /v1/user/login`: Autenticação e recebimento de cookies.
*   `POST /v1/user/logout`: Remove os cookies de autenticação.
*   `POST /v1/user/refresh`: Atualiza o access token.
*   `GET /v1/user/me`: Dados do usuário logado.
*   `POST /v1/user/verify-email`: Verificação de email.
*   `POST /v1/user/forgot-password`: Solicita redefinição de senha.
*   `POST /v1/user/reset-password`: Redefine a senha.

### Relatórios
*   `POST /v1/user/generate-report`: Inicia a geração de um relatório para um vídeo do YouTube.
*   `GET /v1/user/reports`: Lista os relatórios do usuário.
*   `GET /v1/user/report/{id}`: Retorna os detalhes de um relatório específico.
*   `GET /v1/user/report/{id}/pdf`: Faz o download do relatório em PDF.
*   `PUT /v1/user/report/{id}`: Atualiza o título de um relatório.
*   `DELETE /v1/user/report/{id}`: Remove um relatório.

### Perguntas e respostas
*   `GET /v1/questions`: Lista as perguntas cadastradas.
*   `POST /v1/user/answer`: Registra a resposta de um usuário.
*   `PUT /v1/user/answer/{id}`: Atualiza uma resposta.
*   `GET /v1/user/answers`: Lista as respostas do usuário.

### OAuth do YouTube
*   `GET /v1/oauth2/login`: Inicia a autorização com a conta do Google.
*   `GET /v1/oauth2/callback`: Conclui a autorização e salva os tokens.

## 🔧 Fluxos Principais

*   O usuário autentica na aplicação com JWT em cookies.
*   O fluxo OAuth conecta a conta do YouTube e salva `access_token`, `refresh_token` e `channel_id`.
*   Ao criar um relatório, o sistema valida se o vídeo pertence ao canal do usuário.
*   Os comentários são coletados do YouTube, processados e enviados ao Gemini.
*   A análise é persistida no PostgreSQL e o cache do Redis é invalidado após atualizações.

## 📌 Observações

*   O projeto usa logging estruturado para rastrear fluxo, rejeições e falhas.
*   As tarefas de geração de relatório rodam em background para não bloquear a requisição principal.
---

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/hugogsmendes/Lenos-IA)


Desenvolvido por [Hugo Mendes](https://github.com/hugogsmendes) como projeto acadêmico para a Fatec Franca.
