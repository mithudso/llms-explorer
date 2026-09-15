#!/usr/bin/env bash
# Boot everything passkey.mjs needs, run it, tear everything down.
#
#   cd site && npm run e2e:passkey        # or: site/tests/e2e/passkey.sh
#
# Manual, local-only. Not collected by pytest and not run in CI: it needs
# Google Chrome, Homebrew postgresql (initdb/pg_ctl/createdb), hub/.venv with
# the api deps, and `npm ci` done in site/. Everything it starts is disposable
# and on loopback:
#   - a throwaway Postgres cluster (initdb into a temp dir, TCP only, $PG_PORT)
#   - the API in dev mode on $API_PORT with an allow-listed environment built
#     here — it never reads api/.env, so it cannot inherit the production
#     DATABASE_URL, and it is never the API on :8790, which is production
#   - `astro dev --background` on $SITE_PORT pointed at that API
# Override PG_PORT / API_PORT / SITE_PORT if the defaults are taken.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
PY="$ROOT/hub/.venv/bin/python"
ASTRO="$ROOT/site/node_modules/.bin/astro"
PG_PORT="${PG_PORT:-5499}"
API_PORT="${API_PORT:-8791}"
SITE_PORT="${SITE_PORT:-4321}"
DEV_DATABASE_URL="postgresql+asyncpg://explorer:explorer@127.0.0.1:$PG_PORT/explorer"
TMP="$(mktemp -d /tmp/passkey-e2e.XXXXXX)"   # short prefix so paths stay readable in logs
LOCK="$ROOT/site/.astro/dev.json"   # astro's one-per-project background-server lock
API_PID=""
ASTRO_PRE_PID=""                     # lock pid before we launched (another session's)
ASTRO_LAUNCHED=""
ASTRO_PID=""

# The pid in astro's lock file, or empty. Ownership of the daemon keys on this,
# never on a log string astro could reword.
lock_pid() {
  [ -f "$LOCK" ] || { echo ""; return; }
  node -p "try{String(JSON.parse(require('fs').readFileSync(process.argv[1],'utf8')).pid||'')}catch{''}" "$LOCK" 2>/dev/null || echo ""
}

# On a non-zero exit, surface every log before the temp dir goes, then kill
# only what this script started: the API by pid, and the astro daemon only if
# the lock still names the pid this run launched (or, if we were interrupted
# mid-launch, whatever booted where nothing was running before).
cleanup() {
  local rc=$?
  set +e
  if [ "$rc" -ne 0 ]; then
    for f in initdb pg alembic api astro; do
      [ -s "$TMP/$f.log" ] && { echo "--- $f.log (tail) ---" >&2; tail -n 40 "$TMP/$f.log" >&2; }
    done
    # The astro daemon writes its own stdout/stderr here, not to astro.log.
    [ -n "$ASTRO_LAUNCHED" ] && [ -s "$ROOT/site/.astro/dev.log" ] && \
      { echo "--- site/.astro/dev.log (tail) ---" >&2; tail -n 40 "$ROOT/site/.astro/dev.log" >&2; }
  fi
  [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null
  local now; now="$(lock_pid)"
  if [ -n "$ASTRO_LAUNCHED" ] && [ -n "$now" ] && [ "$now" != "$ASTRO_PRE_PID" ] && \
     { [ -z "$ASTRO_PID" ] || [ "$now" = "$ASTRO_PID" ]; }; then
    (cd "$ROOT/site" && "$ASTRO" dev stop >/dev/null 2>&1)
  fi
  pg_ctl -D "$TMP/pg" stop -m fast >/dev/null 2>&1
  rm -rf "$TMP"
  return "$rc"
}
trap cleanup EXIT
trap 'trap - EXIT; cleanup; exit 130' INT
trap 'trap - EXIT; cleanup; exit 143' TERM

die() { echo "passkey.sh: $*" >&2; exit 2; }

# Poll a command every 0.5 s up to N times; fail closed so a boot that never
# happens is reported here, not as a puppeteer timeout minutes later.
wait_for() {
  local tries="$1"; shift
  for _ in $(seq 1 "$tries"); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 0.5
  done
  return 1
}
api_up()  { [ "$(curl -s --max-time 2 -o /dev/null -w '%{http_code}' "http://localhost:$API_PORT/api/me")" = 401 ]; }
site_up() { curl -sf --max-time 5 -o /dev/null "http://localhost:$SITE_PORT/login/"; }

# Prerequisites, checked up front so a missing tool is one clear line.
for tool in initdb pg_ctl pg_isready createdb curl lsof node openssl; do
  command -v "$tool" >/dev/null || die "$tool not on PATH"
done
[ -x "$PY" ]    || die "$PY missing; create hub/.venv with the api deps"
[ -x "$ASTRO" ] || die "$ASTRO missing; run 'npm ci' in site/ first"
for port in "$PG_PORT" "$API_PORT" "$SITE_PORT"; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    die "port $port is already in use; set PG_PORT/API_PORT/SITE_PORT"
  fi
done

echo "== postgres on :$PG_PORT"
initdb -D "$TMP/pg" -U explorer --auth=trust -E UTF8 >"$TMP/initdb.log" 2>&1
pg_ctl -D "$TMP/pg" -o "-p $PG_PORT -c listen_addresses=127.0.0.1 -c unix_socket_directories=''" \
  -l "$TMP/pg.log" start >/dev/null
wait_for 20 pg_isready -q -h 127.0.0.1 -p "$PG_PORT" || die "postgres never accepted connections on :$PG_PORT"
# Same allow-list as the API below: an inherited PGSSLMODE/PGSERVICE/PGOPTIONS
# would otherwise steer libpq/asyncpg away from the throwaway cluster.
env -i PATH="$PATH" HOME="$HOME" createdb -h 127.0.0.1 -p "$PG_PORT" -U explorer explorer
(cd "$ROOT/api" && env -i PATH="$PATH" HOME="$HOME" DATABASE_URL="$DEV_DATABASE_URL" \
  "$PY" -m alembic upgrade head >"$TMP/alembic.log" 2>&1)

echo "== api on :$API_PORT (dev, rp id localhost)"
# `env -i`: an allow-list, not the caller's shell. Nothing from api/.env or the
# operator's environment reaches the API; every value it needs is named here.
(cd "$ROOT/api" && exec env -i PATH="$PATH" HOME="$HOME" \
  DATABASE_URL="$DEV_DATABASE_URL" \
  SESSION_SECRET="$(openssl rand -hex 32)" \
  STRIPE_SECRET_KEY="sk_test_passkey_e2e_placeholder" \
  STRIPE_WEBHOOK_SECRET="whsec_passkey_e2e_placeholder" \
  ENVIRONMENT=dev \
  WEBAUTHN_RP_ID=localhost \
  WEBAUTHN_ORIGINS="http://localhost:$SITE_PORT" \
  SITE_ORIGINS="http://localhost:$SITE_PORT" \
  ALLOWED_HOSTS="localhost,127.0.0.1" \
  API_PUBLIC_URL="http://localhost:$API_PORT" \
  STORES_ROOT="$TMP/stores" \
  "$PY" -m uvicorn explorer_api.main:app --host 127.0.0.1 --port "$API_PORT" >"$TMP/api.log" 2>&1) &
API_PID=$!
# /api/me answers 401 once the app is up; anything else means still booting.
# A settings or import error kills uvicorn at once, so check it is alive too.
for _ in $(seq 1 120); do
  kill -0 "$API_PID" 2>/dev/null || die "api exited during boot"
  api_up && break
  sleep 0.5
done
api_up || die "api never answered on :$API_PORT"

echo "== astro dev on :$SITE_PORT"
# astro keeps one background server per project. `--background` adopts a live
# one instead of starting ours, and stopping it on cleanup would kill another
# session's server, so refuse up front while the lock names a live pid.
ASTRO_PRE_PID="$(lock_pid)"
if [ -n "$ASTRO_PRE_PID" ] && kill -0 "$ASTRO_PRE_PID" 2>/dev/null; then
  die "an astro dev server (pid $ASTRO_PRE_PID) is already running for site/; stop it first"
fi
ASTRO_LAUNCHED=1
(cd "$ROOT/site" && PUBLIC_API_URL="http://localhost:$API_PORT" \
  "$ASTRO" dev --background --host localhost --port "$SITE_PORT" >"$TMP/astro.log" 2>&1)
ASTRO_PID="$(lock_pid)"
[ -n "$ASTRO_PID" ] && [ "$ASTRO_PID" != "$ASTRO_PRE_PID" ] || die "astro dev --background left no lock of its own"
# Cold start runs Vite dep-optimisation over @huggingface/transformers; allow 2 min.
wait_for 240 site_up || die "astro dev never served /login/ on :$SITE_PORT"

echo "== test"
SITE="http://localhost:$SITE_PORT" API="http://localhost:$API_PORT" node "$HERE/passkey.mjs"
