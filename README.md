# Lenos-IA

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini)](https://deepmind.google/technologies/gemini/)
[![YouTube API](https://img.shields.io/badge/YouTube_API-FF0000?style=for-the-badge&logo=youtube)](https://developers.google.com/youtube/v3)

## 📝 Descrição

O **Lenos-IA** é uma plataforma de backend robusta desenvolvida para automatizar a análise de feedback em vídeos do YouTube. Utilizando o poder do **Google Gemini AI**, o sistema extrai e processa comentários para gerar relatórios detalhados sobre o sentimento da audiência, temas recorrentes e métricas comportamentais.

Este projeto foi concebido como um trabalho de graduação (Fatec Franca) e foca em fornecer insights acionáveis para criadores de conteúdo, permitindo uma compreensão profunda da recepção de seus vídeos de forma rápida e precisa.

## ✨ Funcionalidades

*   **Autenticação Segura:** Registro e login de usuários com JWT armazenados em cookies HttpOnly e Secure.
*   **Análise de Vídeos:** Extração automática de comentários via YouTube Data API.
*   **Inteligência Artificial:** Geração de relatórios analíticos utilizando Google Gemini.
*   **Relatórios Personalizados:** Visualização, atualização e exclusão de análises anteriores.
*   **Notificações por E-mail:** Verificação de conta.
*   **Rate Limiting:** Proteção de endpoints sensíveis utilizando SlowAPI.
*   **Processamento Assíncrono:** Tarefas pesadas (análise de IA) executadas em background para maior fluidez.

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

## 🏗️ Arquitetura do Projeto

O projeto segue um padrão de **Arquitetura em Camadas (Layered Architecture)** para garantir manutenibilidade e escalabilidade:

1.  **Routes (`api/routes/`)**: Define os endpoints da API e lida com as requisições/respostas HTTP.
2.  **Services (`service/`)**: Contém a lógica de negócio, orquestrando repositórios e serviços externos (Gemini, YouTube).
3.  **Repositories (`repository/`)**: Camada de acesso a dados responsável pelas queries SQLAlchemy.
4.  **Models (`models/`)**: Definição das tabelas e entidades do banco de dados.
5.  **Utils (`utils/`)**: Schemas de validação, exceções customizadas e utilitários de segurança.

### Estrutura de Diretórios

```text
/
├── alembic/            # Scripts de migração de banco de dados
├── api/
│   └── routes/         # Endpoints: user, report, question, answer
├── app/
│   └── main.py         # Inicialização do FastAPI e roteamento
├── database/           # Configuração de conexões (Postgres, Redis)
├── models/             # Modelos ORM do SQLAlchemy
├── repository/         # Camada de persistência de dados
├── service/            # Lógica de negócio e integrações
├── tests/              # Testes automatizados com Pytest
├── utils/              # Schemas Pydantic e middlewares
└── alembic.ini         # Configuração do Alembic
```

## 🚀 Instalação e Execução

### Pré-requisitos

*   Python 3.12+
*   PostgreSQL
*   Redis
*   Chaves de API (Google Cloud e Resend)

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/lenos-ia.git
    cd lenos-ia
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate   # Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:
    ```bash
    cp .env.example .env
    ```
    Preencha as chaves:
    *   `key_youtube`: Chave da API do Google Cloud (YouTube Data API v3)
    *   `key_gemini`: Chave da API do Google Gemini
    *   `DATABASE_URL_ASYNC`: Ex: `postgresql+asyncpg://user:pass@localhost/dbname`
    *   `REDIS_URL`: Ex: `redis://localhost:6379`

5.  **Execute as migrações:**
    ```bash
    alembic upgrade head
    ```

6.  **Inicie a aplicação:**
    ```bash
    uvicorn app.main:app --reload
    ```

## 📡 API Endpoints (Principais)

### Autenticação (`/v1`)
*   `POST /register`: Registro de novo usuário.
*   `POST /login`: Autenticação e recebimento de cookies.
*   `GET /me`: Dados do usuário logado.
*   `GET /verify_email`: Validação de conta via token.

### Relatórios (`/v1/user`)
*   `POST /generate_report`: Inicia análise de um vídeo (Background Task).
*   `GET /reports`: Lista todos os relatórios do usuário.
*   `GET /report/{id}`: Detalhes de um relatório específico.
*   `DELETE /delete_report/{id}`: Remove um relatório.

### Perguntas e Respostas (`/v1`)
*   `POST /create_question`: Cria uma nova pergunta de feedback.
*   `POST /user/answer_question`: Registra a resposta do usuário a uma pergunta.

## 🛠️ Melhorias Futuras

*   [ ] Dashboard visual para métricas agregadas.
*   [ ] Suporte para análise de múltiplos vídeos simultaneamente.
*   [ ] Integração com outras redes sociais (TikTok, Instagram).

---

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/hugogsmendes/Lenos-IA)
Desenvolvido por [Hugo Mendes](https://github.com/hugomendes) como projeto acadêmico para a Fatec Franca.
