"""Turns the k6 summaries and docker stats samples into a Markdown report. Usage: python3 report.py results/"""

import json
import re
import sys
from pathlib import Path

RESULTS = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
ROOT = Path(__file__).resolve().parent.parent
RAILS_ROOT = ROOT.parent / "controlfinan-rails8-hotwire"
APPS = {"rails": "Rails 8.1 + Hotwire (Puma)", "django": "Django 5.2 (Gunicorn)"}
PAGES = {
    "lista": "Conta Corrente (30 itens + saldo)",
    "dia": "Saldo do dia (filtro)",
    "dashboard": "Dashboard do mês",
    "json": "API JSON (30 itens)",
    "criar": "Criar lançamento (POST)",
}


def mib(text):
    value, unit = re.match(r"([\d.]+)\s*([KMG]?i?B)", text.strip()).groups()
    factors = {"B": 1 / 1024 / 1024, "KiB": 1 / 1024, "MiB": 1, "GiB": 1024, "kB": 1 / 1000, "MB": 1, "GB": 1000}
    return float(value) * factors[unit]


def k6(app, page):
    data = json.loads((RESULTS / f"{app}-{page}.json").read_text())["metrics"]
    duration = data["http_req_duration{phase:load}"]["values"]
    return {
        "rps": data["http_reqs{phase:load}"]["values"]["count"] / 30,
        "p50": duration["p(50)"],
        "p95": duration["p(95)"],
        "p99": duration["p(99)"],
        "errors": data["http_req_failed{phase:load}"]["values"]["rate"] * 100,
    }


def stats(app, page):
    lines = [line.split(";") for line in (RESULTS / f"{app}-{page}-stats.txt").read_text().splitlines() if ";" in line]
    # Ignore samples taken while the container was stopping (0B of memory).
    lines = [(cpu, mem) for cpu, mem in lines if mib(mem.split("/")[0]) > 0]
    cpu = [float(c.strip("%")) for c, _ in lines]
    mem = [mib(m.split("/")[0]) for _, m in lines]
    return {"cpu_avg": sum(cpu) / len(cpu), "mem_peak": max(mem)}


def lines_of_code(root, patterns, exclude=()):
    total = 0
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and not any(part in str(path) for part in exclude):
                total += sum(1 for line in path.read_text(errors="ignore").splitlines() if line.strip())
    return total


def winner(values, higher_is_better):
    best = max(values, key=values.get) if higher_is_better else min(values, key=values.get)
    other = next(app for app in values if app != best)
    ratio = values[best] / values[other] if higher_is_better else values[other] / values[best]
    return f"{best.capitalize()} ({ratio:.1f}x)"


def main():
    out = ["# Benchmark: ControlFinan em Rails 8 + Hotwire x Django", ""]
    out += [
        "Mesmo app (paridade de telas e regras), mesmos dados (7.174 lançamentos), modo produção.",
        "Cada app: 2 processos × 5 threads, limitado a 2 CPUs e 1 GB de RAM; Postgres 16 próprio (2 CPUs).",
        "Carga: k6 com 20 usuários simultâneos, 10 s de aquecimento + 30 s medidos por tela, logado de verdade.",
        "",
        "## Requisições por segundo e latência",
        "",
        "| Tela | App | req/s | p50 (ms) | p95 (ms) | p99 (ms) | erros | CPU média | memória pico |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    summary = {}
    for page, label in PAGES.items():
        rps = {}
        for app in APPS:
            r, s = k6(app, page), stats(app, page)
            rps[app] = r["rps"]
            flag = " ⚠️ inválido" if r["errors"] > 1 else ""
            out.append(
                f"| {label} | {app.capitalize()}{flag} | {r['rps']:.0f} | {r['p50']:.1f} | {r['p95']:.1f} | {r['p99']:.1f} | "
                f"{r['errors']:.1f}% | {s['cpu_avg']:.0f}% | {s['mem_peak']:.0f} MiB |"
            )
        summary[label] = winner(rps, higher_is_better=True)

    out += ["", "## Quem foi mais rápido (req/s)", "", "| Tela | Mais rápido |", "|---|---|"]
    out += [f"| {label} | {result} |" for label, result in summary.items()]

    meta = {app: json.loads((RESULTS / f"{app}-meta.json").read_text()) for app in APPS}
    out += ["", "## Boot, memória e imagem", "", "| | Rails | Django |", "|---|---:|---:|"]
    out.append(
        f"| Subir até responder `/up` (inclui migrations) | {meta['rails']['boot_seconds']:.1f} s | "
        f"{meta['django']['boot_seconds']:.1f} s |"
    )
    out.append(
        f"| Memória parado (2 processos) | {mib(meta['rails']['idle_memory']):.0f} MiB | "
        f"{mib(meta['django']['idle_memory']):.0f} MiB |"
    )
    out.append(
        f"| Tamanho da imagem Docker | {meta['rails']['image_bytes'] / 1e6:.0f} MB | "
        f"{meta['django']['image_bytes'] / 1e6:.0f} MB |"
    )

    rails_code = lines_of_code(
        RAILS_ROOT,
        [
            "app/**/*.rb",
            "app/**/*.erb",
            "app/**/*.jbuilder",
            "app/javascript/**/*.js",
            "app/assets/stylesheets/*.css",
            "config/routes.rb",
        ],
    )
    django_code = lines_of_code(
        ROOT,
        [
            "finance/**/*.py",
            "finance/**/*.html",
            "finance/**/*.txt",
            "finance/static/finance/js/*.js",
            "finance/assets/app.tailwind.css",
            "config/urls.py",
        ],
        exclude=("migrations",),
    )
    django_tests = lines_of_code(ROOT, ["tests/*.py"])
    out += ["", "## Código", "", "| | Rails | Django |", "|---|---:|---:|"]
    out.append(f"| Linhas de código do app (sem linhas em branco) | {rails_code} | {django_code} |")
    out.append(f"| Linhas de teste | 0 | {django_tests} |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
