# ControlFinan (Django)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)

Aplicação web para controle financeiro pessoal, pensada para quem trabalha como motorista de aplicativo. Cada usuário registra entradas (créditos) e saídas (débitos) em contas como dinheiro, bancos e carteiras de aplicativos, e acompanha o saldo por dia e por mês.

Esta é a versão em **Django** do [ControlFinan em Rails 8 + Hotwire](https://github.com/igorcb/controlfinan-rails8-hotwire), com **paridade de funcionalidades e de visual**: mesmas telas, mesmas regras, mesmas mensagens e o **mesmo esquema de banco** (as duas versões podem usar os mesmos dados, inclusive as senhas).

## Sumário

- [Funcionalidades](#funcionalidades)
- [Como a paridade foi feita](#como-a-paridade-foi-feita)
- [Benchmark](#benchmark)
- [Como rodar com Docker](#como-rodar-com-docker)
- [Testes](#testes)
- [Estrutura](#estrutura)
- [Licença](#licença)

## Funcionalidades

| Tela | Rota | O que faz |
|---|---|---|
| Conta Corrente | `/` | Lista os lançamentos, do mais recente para o mais antigo, 30 por página, com o saldo total |
| Saldo do dia | `/?date=AAAA-MM-DD` | Filtra a listagem por um dia e mostra o saldo daquele dia |
| Novo lançamento | `/current_accounts/new` | Cadastra um crédito ou um débito |
| Detalhe, edição e exclusão | `/current_accounts/:id` | Mostra, altera ou remove um lançamento |
| Dashboard | `/dashboard` | Abas **Saldo Diário** (saldo de cada dia do mês) e **Saldo Mensal** (corridas menos combustível, lavagem e telefone). As setas navegam entre os meses |
| JSON | `/current_accounts.json` e `/current_accounts/:id.json` | Os mesmos dados, para integrações |
| Cadastro, login e senha | `/registration/new`, `/session/new`, `/passwords/new` | Conta de usuário, com senha de no mínimo 6 caracteres |

Cada usuário só enxerga os próprios lançamentos.

## Como a paridade foi feita

| Rails 8 + Hotwire | Django |
|---|---|
| Autenticação nativa do Rails 8 (`has_secure_password`, tabela `sessions`, cookie assinado `session_id`) | Mesmo modelo: tabela `sessions`, cookie assinado `session_id` e senhas em **bcrypt no formato do Rails** (`$2a$`) |
| `rate_limit to: 10, within: 3.minutes` | Limite de 10 tentativas a cada 3 minutos por IP, contado no cache |
| Token de redefinição de senha (15 minutos) | Token assinado com validade de 15 minutos, invalidado ao trocar a senha |
| Turbo (`data-turbo-confirm`) e Stimulus (abas) | JavaScript simples para a confirmação e as abas |
| jbuilder | `JsonResponse` com os mesmos campos e o mesmo formato |
| Tailwind CSS 4 | Tailwind CSS 4 (CLI standalone), com as mesmas classes |

**Verificação**, com o mesmo usuário e os mesmos dados nos dois apps:

- 15 telas com texto idêntico, incluindo paginação, filtro por dia, datas inválidas e o dashboard em meses diferentes.
- Lista, dashboard e formulário idênticos **pixel a pixel**, no celular (390 px) e no computador.
- Mesmo resultado em criar, editar e excluir, mensagens de validação, login inválido, erros de cadastro e JSON.

## Benchmark

O benchmark que compara as nove versões do ControlFinan (Rails, Django, Laravel, Go, Java, Rust, C#, Node.js e Elixir), com os mesmos dados e os mesmos limites de CPU e memória, fica no repositório do app de referência: [controlfinan-rails8-hotwire/benchmark](https://github.com/igorcb/controlfinan-rails8-hotwire/tree/main/benchmark).

## Como rodar com Docker

Pré-requisitos: Docker e Docker Compose.

```bash
cp .env.example .env   # defina DJANGO_SECRET_KEY
docker compose up -d
```

O container gera o CSS, roda as migrations e sobe o servidor. Abra http://localhost:8001. Para criar o primeiro usuário, acesse `/registration/new`.

| Ação | Comando |
|---|---|
| Ver logs | `docker compose logs -f web` |
| Shell do Django | `docker compose exec web python manage.py shell` |
| Rodar migrations | `docker compose exec web python manage.py migrate` |
| Testes | `docker compose exec web pytest` |
| Lint | `docker compose exec web ruff check .` |
| Parar e apagar o banco | `docker compose down -v` |

Em desenvolvimento os e-mails (redefinição de senha) aparecem no log do container.

## Testes

Testes automatizados com **pytest + pytest-django** (no lugar do RSpec) e **factory_boy** (no lugar do FactoryBot):

```bash
docker compose exec web pytest
```

Os 53 testes cobrem:

- **Modelos:** validações com as mesmas mensagens do Rails, saldos e senha bcrypt compatível com o Rails.
- **Acesso:** login, logout, cadastro, limite de tentativas e redefinição de senha por e-mail.
- **Lançamentos:** listagem, filtro, paginação, CRUD e isolamento entre usuários.
- **JSON e dashboard.**

## Estrutura

```
config/                     settings e rotas
finance/models.py           User, Session e CurrentAccount (mesmas tabelas do Rails)
finance/auth.py             sessão por cookie assinado, login obrigatório e rate limit
finance/views/              lançamentos, dashboard, login, cadastro e senha
finance/templates/finance/  telas (mesmo HTML/Tailwind do Rails)
finance/assets/             fonte do Tailwind
finance/static/finance/     JS e ícones
tests/                      testes com pytest e factory_boy
Dockerfile.prod             imagem de produção (Gunicorn + WhiteNoise)
```

## Licença

Distribuído sob a licença [MIT](LICENSE).
