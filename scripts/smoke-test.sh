#!/usr/bin/env bash
# Run after `docker compose up -d`. Checks that each service answers.
fail=0

check() {
  name="$1"; shift
  if "$@" > /dev/null 2>&1; then echo "OK    $name"; else echo "FAIL  $name"; fail=1; fi
}

check "web        (3000)"  curl -sf http://localhost:3000
check "api health (8000)"  curl -sf http://localhost:8000/health
check "chain rpc  (8545)"  curl -sf -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' http://localhost:8545
check "ollama    (11434)"  curl -sf http://localhost:11434/api/tags

exit $fail
