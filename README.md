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
- [Benchmark: Rails x Django](#benchmark-rails-x-django)
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

## Benchmark: Rails x Django

Mesmo app (paridade de telas e regras) e mesmos dados (7.174 lançamentos), os dois em **modo produção**:

- **Rails 8.1** com Puma (Ruby 3.4 com YJIT, padrão do Rails 8) e **Django 5.2** com Gunicorn `gthread` (Python 3.12).
- Cada app com **2 processos × 5 threads**, limitado a **2 CPUs e 1 GB de RAM**, cada um com o seu Postgres 16 (2 CPUs).
- Carga com **k6**: 20 usuários simultâneos, logados de verdade pelo formulário de login, 10 s de aquecimento e 30 s medidos por tela.

### Requisições por segundo e latência


| Tela | App | req/s | p50 (ms) | p95 (ms) | p99 (ms) | erros | CPU média | memória pico |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Conta Corrente (30 itens + saldo) | Rails | 104 | 193.8 | 244.1 | 286.4 | 0.0% | 191% | 264 MiB |
| Conta Corrente (30 itens + saldo) | Django | 84 | 238.4 | 286.2 | 592.5 | 0.0% | 195% | 103 MiB |
| Saldo do dia (filtro) | Rails | 251 | 79.1 | 95.7 | 110.5 | 0.0% | 192% | 272 MiB |
| Saldo do dia (filtro) | Django | 123 | 118.7 | 394.3 | 447.1 | 0.0% | 200% | 103 MiB |
| Dashboard do mês | Rails | 169 | 113.2 | 175.1 | 193.0 | 0.0% | 194% | 276 MiB |
| Dashboard do mês | Django | 129 | 130.4 | 361.2 | 440.0 | 0.0% | 198% | 106 MiB |
| API JSON (30 itens) | Rails | 304 | 63.9 | 81.8 | 109.1 | 0.0% | 188% | 299 MiB |
| API JSON (30 itens) | Django | 253 | 52.4 | 150.1 | 405.1 | 0.0% | 196% | 106 MiB |
| Criar lançamento (POST) | Rails | 403 | 49.1 | 60.7 | 66.0 | 0.0% | 203% | 312 MiB |
| Criar lançamento (POST) | Django | 253 | 56.3 | 173.0 | 207.6 | 0.0% | 201% | 106 MiB |

## Quem foi mais rápido (req/s)

| Tela | Mais rápido |
|---|---|
| Conta Corrente (30 itens + saldo) | Rails (1.2x) |
| Saldo do dia (filtro) | Rails (2.0x) |
| Dashboard do mês | Rails (1.3x) |
| API JSON (30 itens) | Rails (1.2x) |
| Criar lançamento (POST) | Rails (1.6x) |

## Boot, memória e imagem

| | Rails | Django |
|---|---:|---:|
| Subir até responder `/up` (inclui migrations) | 4.9 s | 2.7 s |
| Memória parado (2 processos) | 125 MiB | 82 MiB |
| Tamanho da imagem Docker | 515 MB | 168 MB |

## Código

| | Rails | Django |
|---|---:|---:|
| Linhas de código do app (sem linhas em branco) | 787 | 1039 |
| Linhas de teste | 0 | 392 |

### Leitura dos resultados

- **Velocidade:** o Rails respondeu mais requisições por segundo em todas as telas (de 1,2x a 2x) e com latência mais estável (p95 e p99 menores). Os dois apps usaram as 2 CPUs inteiras, então o limite foi o processamento do próprio app.
- **Recursos:** o Django subiu mais rápido, usou cerca de 3x menos memória e gerou uma imagem Docker 3x menor.
- **Ressalvas:** uma rodada, numa máquina de desenvolvimento. O Ruby roda com YJIT (JIT ligado por padrão no Rails 8) e o Python 3.12 sem JIT. Cada stack usou a configuração padrão de produção.

### Rodar o benchmark

Com o [Rails Hotwire](https://github.com/igorcb/controlfinan-rails8-hotwire) clonado ao lado deste repositório e o banco de desenvolvimento dele no ar (fonte dos dados compartilhados):

```bash
./benchmark/run.sh
```

O resultado fica em `benchmark/results/RESULTS.md`.

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
benchmark/                  benchmark Rails x Django (Docker Compose + k6)
Dockerfile.prod             imagem de produção (Gunicorn + WhiteNoise)
```

## Licença

Distribuído sob a licença [MIT](LICENSE).
