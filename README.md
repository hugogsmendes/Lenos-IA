# Lenos-IA

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-4169E1?style=for-the-badge&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic)](https://pydantic.dev/docs/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)](https://redis.io/docs/latest/integrate/redis-py/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=googlegemini)](https://ai.google.dev/gemini-api/docs?hl=pt-br)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube)](https://developers.google.com/youtube/v3)
[![Resend](https://img.shields.io/badge/Resend-000000?style=for-the-badge&logo=resend)](https://resend.com/docs/send-with-fastapi)


O **Lenos IA** é uma API para criadores analisarem a recepção de vídeos do YouTube. A aplicação conecta a conta do criador via OAuth 2.0, valida a propriedade do vídeo, coleta os comentários e usa o Google Gemini para gerar relatórios analíticos.

Esta versão amplia o ciclo de vida dos relatórios com métricas de sentimento, temas recorrentes, recomendações estratégicas, estatísticas por período, cota mensal e exportação em PDF.

## Funcionalidades

- Autenticação e autorização com JWT em cookies HttpOnly.
- Registro, verificação de e-mail, recuperação de senha e alteração de e-mail com confirmação por token.
- Conexão OAuth 2.0 com o YouTube e consulta do status da conexão.
- Validação de que o vídeo informado pertence ao canal conectado pelo usuário.
- Coleta paginada de comentários pela YouTube Data API.
- Geração assíncrona de relatórios com Google Gemini.
- Persistência das métricas de comentários processados, positivos e negativos.
- Persistência de temas recorrentes e recomendações em JSONB.
- Listagem de relatórios com filtros por status e intervalo de datas, incluindo métricas agregadas.
- Cota mensal de cinco relatórios concluídos por usuário.
- Exportação do relatório em PDF com Markdown, tabelas, temas e recomendações.
- Cache de consultas com Redis e invalidação após alterações.
- Rate limiting nas rotas sensíveis.
- Logging estruturado para fluxo de negócio, rejeições e falhas inesperadas.

## Arquitetura

O projeto utiliza arquitetura em camadas. As rotas recebem e respondem pelas requisições HTTP; os serviços concentram as regras de negócio; os repositórios acessam os dados; e os modelos representam as entidades persistidas.

```text
Cliente HTTP
    |
    v
src/api/routes/       Endpoints, dependências e contratos HTTP
    |
    v
src/service/          Regras de negócio e integrações externas
    |
    +--> Google Gemini
    +--> YouTube Data API / OAuth 2.0
    +--> Resend
    |
    v
src/repository/       Consultas e comandos de persistência
    |
    +--> PostgreSQL
    +--> Redis
```

### Estrutura de diretórios

```text
.
├── alembic/                 # Migrações do banco de dados
├── src/
│   ├── api/routes/          # Rotas FastAPI
│   ├── app/                 # Inicialização da aplicação
│   ├── database/            # Clientes PostgreSQL e Redis
│   ├── middlewares/         # Middlewares, incluindo logging HTTP
│   ├── models/              # Entidades SQLAlchemy
│   ├── repository/          # Camada de acesso a dados
│   ├── service/             # Regras de negócio e integrações
│   └── utils/               # Schemas, segurança, exceções e helpers
├── alembic.ini
└── requirements.txt
```

## Stack

| Tecnologia | Uso no projeto |
| :--- | :--- |
| FastAPI | API HTTP assíncrona e documentação OpenAPI |
| SQLAlchemy Async + asyncpg | ORM e acesso assíncrono ao PostgreSQL |
| Alembic | Migrações de schema |
| Redis | Cache de consultas de relatórios |
| Google Gemini | Geração da análise dos comentários |
| YouTube Data API | Consulta de vídeos, canais e comentários |
| Google OAuth 2.0 | Conexão segura da conta do YouTube |
| FPDF2 | Exportação de relatórios em PDF |
| Pydantic + Pydantic Settings | Validação de dados e configuração |
| Argon2 + PyJWT | Hash de senha e autenticação por tokens |
| Resend | E-mails transacionais |
| SlowAPI | Rate limiting |
| HTTPX | Requisições HTTP assíncronas |

## Fluxo de relatório

1. O usuário conecta seu canal do YouTube pelo OAuth 2.0.
2. O usuário envia a URL de um vídeo para `POST /v1/user/generate-report`.
3. A API valida a URL, a conexão OAuth, a cota mensal e a propriedade do vídeo.
4. São criados uma análise e um relatório com status pendente.
5. Uma tarefa em background coleta, processa e envia os comentários ao Gemini.
6. O resultado é persistido com métricas, temas recorrentes e recomendações; em caso de falha, análise e relatório são marcados como `failed`.
7. O relatório pode ser consultado pela API ou exportado como PDF.

## Rotas

### Saúde

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/health` | Verifica se a API está em execução. |

### Conta e autenticação

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `POST` | `/v1/user/register` | Cria uma conta e envia o e-mail de verificação. |
| `POST` | `/v1/user/login` | Autentica o usuário e define cookies JWT. |
| `POST` | `/v1/user/logout` | Remove os cookies de autenticação. |
| `POST` | `/v1/user/refresh` | Renova o access token. |
| `GET` | `/v1/user/me` | Retorna os dados do usuário autenticado. |
| `PUT` | `/v1/user` | Atualiza dados cadastrais. |
| `PUT` | `/v1/user/password` | Atualiza a senha do usuário. |
| `DELETE` | `/v1/user` | Exclui a conta do usuário. |
| `POST` | `/v1/user/verify-email` | Confirma o e-mail de cadastro. |
| `POST` | `/v1/user/forgot-password` | Envia e-mail para redefinição de senha. |
| `POST` | `/v1/user/reset-password` | Redefine a senha a partir de um token. |
| `POST` | `/v1/user/email` | Solicita a alteração de e-mail. |
| `POST` | `/v1/user/confirm-email` | Confirma a alteração de e-mail e renova os cookies JWT. |

### OAuth do YouTube

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/v1/oauth2/login` | Redireciona para a autorização OAuth do YouTube. |
| `GET` | `/v1/oauth2/callback` | Salva os tokens e redireciona para o dashboard. |
| `GET` | `/v1/oauth2/status` | Retorna se a conta está conectada e se o refresh token expirou. |

### Relatórios

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `POST` | `/v1/user/generate-report` | Inicia a geração assíncrona de um relatório. |
| `GET` | `/v1/user/reports` | Lista relatórios e estatísticas por período. Requer `start_date` e `end_date`; aceita `status` opcional. |
| `GET` | `/v1/user/reports/quota` | Retorna uso, limite, saldo e comentários processados no mês. |
| `GET` | `/v1/user/report/{id}` | Retorna o relatório, métricas, temas e recomendações. |
| `GET` | `/v1/user/report/{id}/pdf` | Exporta o relatório em PDF. |
| `PUT` | `/v1/user/report/{id}` | Atualiza o título do relatório. |
| `DELETE` | `/v1/user/report/{id}` | Exclui o relatório e sua análise associada. |

### Perguntas e respostas

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/v1/questions` | Lista as perguntas disponíveis. |
| `POST` | `/v1/user/answer` | Registra uma resposta do usuário. |
| `PUT` | `/v1/user/answer/{id}` | Atualiza uma resposta do usuário. |
| `GET` | `/v1/user/answers` | Lista as respostas do usuário autenticado. |

## Observações

- As rotas protegidas dependem do cookie `access_token`.
- A documentação interativa é disponibilizada pelo FastAPI nos ambientes da aplicação.
- A API utiliza PostgreSQL, Redis, Google Cloud, Gemini e Resend como serviços externos.
---

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/hugogsmendes/Lenos-IA)


Desenvolvido por [Hugo Mendes](https://github.com/hugogsmendes) como projeto acadêmico para a Fatec Franca.
