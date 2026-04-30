# News Briefing (Projeto Prático #01)

Sistema em **Python** com **Agno** que:
- conduz uma **entrevista no Discord** (DM) para coletar tópicos, palavras-chave, limites, e-mail e ID do canal;
- em horário agendado, **busca notícias (RSS do Google News)**, **gera o briefing** com o modelo configurado (Groq via Agno) e **entrega no canal do Discord e por e-mail** (SMTP opcional).

Dados de configuração ficam no **PostgreSQL** (acesso assíncrono com SQLAlchemy + asyncpg).

## Requisitos

- Python 3.10+ (recomendado 3.12, como no Docker)
- Conta [Discord Developer Portal](https://discord.com/developers/applications) (bot + intents)
- Chave de provedor LLM para o Agno (**Groq**)
- **PostgreSQL** 15+ (local ou contêiner)

## Estrutura (resumo)

- `src/news_briefing/domain/` — modelos puros
- `src/news_briefing/ports/` — interfaces (repositório, notícias, geração, entrega)
- `src/news_briefing/application/` — `run_briefing_job`
- `src/news_briefing/adapters/` — Discord, Agno, RSS, SMTP, persistência
- `src/news_briefing/scheduler/` — APScheduler (cron diário)
- `src/news_briefing/main.py` — bootstrap
- `Dockerfile` + `docker-compose.yml` — app + Postgres

## Configuração

1. Copie `.env.example` para `.env` e preencha **DISCORD_BOT_TOKEN**, **LLM_PROVIDER=groq** e a chave:
   - preferencial: `LLM_API_KEY`
   - ou `GROQ_API_KEY`
2. No portal do Discord, ative **Message Content Intent** (Privileged Gateway Intents) e convide o bot com o escopo `bot` e `applications.commands`.
3. Ajuste horário: `BRIEFING_SCHEDULE_HOUR`, `BRIEFING_SCHEDULE_MINUTE`, `SCHEDULE_TIMEZONE`.
4. Para e-mail, defina `SMTP_HOST`, `SMTP_PORT`, `MAIL_FROM` e, se necessário, `SMTP_USER` / `SMTP_PASSWORD`. Sem SMTP, o resumo ainda é postado no Discord.

## Uso (local, sem Docker)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
# Suba o Postgres e ajuste DATABASE_URL no .env, depois:
python -m news_briefing
```

No servidor, use o comando de barra **`/briefing`**. O bot abre a conversa no **privado**; ao final, o assistente chama a ferramenta `record_user_preferences` e grava no banco.

## Uso (Docker)

```bash
cp .env.example .env
# Preencha DISCORD_BOT_TOKEN, LLM_PROVIDER=groq, LLM_API_KEY (ou GROQ_API_KEY), etc.
docker compose up --build
```

- O serviço `db` sobe o Postgres; o `app` aguarda o healthcheck e cria tabelas automaticamente.
- `DATABASE_URL` aponta para o host `db` dentro da rede do Compose.
- A porta `5432` fica publicada no host (útil para inspeção com DBeaver ou `psql`).

### Trigger manual de teste (sem esperar horario)

Com os containers rodando, dispare o envio imediatamente:

```bash
docker compose exec app python scripts/trigger_now.py
```

O script varre as configuracoes salvas no banco e executa um ciclo completo
(buscar noticias -> gerar briefing -> enviar no Discord/e-mail).

### Teste SMTP isolado (fora do container)

Para validar apenas o envio de e-mail com o `.env`:

```bash
python scripts/send_test_email.py --to seu_email@exemplo.com
```

Sem `--to`, o script usa `MAIL_FROM` como destino.

## Onde rodar o bot

- O contêiner **não expõe** a porta do processo: o worker do Discord só abre a conexão de saída com a API do Discord. Não é necessário mapear `ports:` no serviço `app` (a não ser que no futuro exista um painel web).

## Dicas

- `DISCORD_GUILD_ID` (não zero) acelera o sync de comandos num servidor de testes.
- ID do canal: Discord → Configurações → Avançado → **Modo desenvolvedor** ativado; clique com o botão direito no canal de texto → **Copiar ID**.

## Licença

Uso acadêmico / projeto da disciplina (ajuste conforme a turma).
# briefing
