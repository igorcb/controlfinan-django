#!/usr/bin/env bash
# Rails 8 + Hotwire vs Django benchmark. Usage: ./benchmark/run.sh
# Needs the Rails repo next to this one (../controlfinan-rails8-hotwire) with its dev database running,
# which provides the shared data (benchmark@exemplo.com and its entries).
set -euo pipefail
cd "$(dirname "$0")"
RAILS_APP="$(cd ../../controlfinan-rails8-hotwire && pwd)"
export RAILS_APP
RAILS_MASTER_KEY="$(cat "$RAILS_APP/config/master.key")"
export RAILS_MASTER_KEY
RESULTS=results
rm -rf "$RESULTS" && mkdir -p "$RESULTS"
compose() { docker compose -p cfbench "$@"; }

echo "== build"
compose build rails django >/dev/null

echo "== shared data (users + current_accounts from the Rails dev database)"
docker exec controlfinan-rails8-hotwire-db-1 pg_dump -U app --data-only -t users -t current_accounts app_development > "$RESULTS/data.sql"

measure_boot() { # $1 service, $2 port -> seconds until /up answers 200
  local start end
  start=$(date +%s.%N)
  compose up -d "$1" >/dev/null 2>&1
  until curl -fs "http://localhost:$2/up" >/dev/null 2>&1; do sleep 0.2; done
  end=$(date +%s.%N)
  echo "$end - $start" | bc
}

sample_stats() { # $1 container, $2 output file; runs until killed
  while true; do docker stats --no-stream --format '{{.CPUPerc}};{{.MemUsage}}' "$1" >> "$2" 2>/dev/null; done
}

for app in rails django; do
  if [ "$app" = rails ]; then port=3101; db=rails-db; dbname=app_production; else port=8101; db=django-db; dbname=controlfinan_django; fi
  echo "== $app"
  compose up -d "$db" >/dev/null 2>&1
  until compose exec -T "$db" pg_isready -U app >/dev/null 2>&1; do sleep 0.5; done
  sleep 2
  boot=$(measure_boot "$app" "$port")
  compose exec -T "$db" psql -U app -d "$dbname" -q -c "SET session_replication_role = replica;" -f - < "$RESULTS/data.sql" >/dev/null
  compose restart "$app" >/dev/null 2>&1   # fresh processes with the data loaded
  until curl -fs "http://localhost:$port/up" >/dev/null 2>&1; do sleep 0.2; done
  sleep 3
  container=$(compose ps -q "$app")
  idle=$(docker stats --no-stream --format '{{.MemUsage}}' "$container" | cut -d/ -f1)
  image=$(docker image inspect "bench-$app" --format '{{.Size}}')
  echo "{\"boot_seconds\": $boot, \"idle_memory\": \"$idle\", \"image_bytes\": $image}" > "$RESULTS/$app-meta.json"
  echo "   boot ${boot}s, idle memory $idle"
  for page in lista dia dashboard json criar; do
    sample_stats "$container" "$RESULTS/$app-$page-stats.txt" & sampler=$!
    compose run --rm -T --user "$(id -u):$(id -g)" -e BASE="http://$app:$([ "$app" = rails ] && echo 3000 || echo 8000)" -e PAGE="$page" -e OUT="/results/$app-$page.json" \
      k6 run --quiet /scripts/scenario.js > "$RESULTS/$app-$page-k6.log" 2>&1 || echo "   (k6 returned an error for $page, see $RESULTS/$app-$page-k6.log)"
    kill "$sampler" 2>/dev/null; wait "$sampler" 2>/dev/null || true
    echo "   $page done"
  done
  compose stop "$app" "$db" >/dev/null 2>&1
done

compose down -v >/dev/null 2>&1
python3 report.py "$RESULTS" | tee "$RESULTS/RESULTS.md"
