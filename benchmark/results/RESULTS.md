# Benchmark: ControlFinan em Rails 8 + Hotwire x Django

Mesmo app (paridade de telas e regras), mesmos dados (7.174 lançamentos), modo produção.
Cada app: 2 processos × 5 threads, limitado a 2 CPUs e 1 GB de RAM; Postgres 16 próprio (2 CPUs).
Carga: k6 com 20 usuários simultâneos, 10 s de aquecimento + 30 s medidos por tela, logado de verdade.

## Requisições por segundo e latência

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
