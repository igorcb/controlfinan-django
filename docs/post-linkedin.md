# Post para o LinkedIn

Reescrevi o mesmo app em Rails 8 e em Django e coloquei os dois para competir. 🏁

O ControlFinan é um app de controle financeiro para motoristas de aplicativo. Fiz uma versão em Django com paridade total com a versão em Rails 8 + Hotwire: mesmas telas (idênticas pixel a pixel), mesmas regras, mesmo banco de dados, e até as senhas criadas em um funcionam no outro.

Depois medi os dois em produção, com as mesmas condições: 2 CPUs, 1 GB de RAM, 2 processos × 5 threads, os mesmos 7 mil lançamentos e 20 usuários simultâneos logados.

⚡ Velocidade: Rails 8 venceu em todas as telas, de 1,2x a 2x mais requisições por segundo, com latência mais estável.
🪶 Recursos: Django subiu quase 2x mais rápido, usou cerca de 3x menos memória e gerou uma imagem Docker 3x menor.

O que eu aprendi:
• O YJIT, ligado por padrão no Rails 8, faz diferença real no Ruby.
• O Django entrega muito com pouca memória, o que pesa quando o servidor é pequeno.
• Benchmark justo dá trabalho. Meu primeiro resultado estava errado por um detalhe de token CSRF no script de teste, não nos frameworks. Meça, desconfie e confira.

Não existe "melhor framework". Existe o melhor para o seu contexto: performance por CPU ou economia de memória?

Stack: Rails 8.1 + Hotwire + Puma | Django 5.2 + Gunicorn | PostgreSQL 16 | Tailwind 4 | k6 | Docker

#Rails #Django #Ruby #Python #Benchmark #WebDevelopment

---

Números completos: [controlfinan-rails8-hotwire/benchmark](https://github.com/igorcb/controlfinan-rails8-hotwire/tree/main/benchmark)
