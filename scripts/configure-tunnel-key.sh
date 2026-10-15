#!/usr/bin/env bash
set +x
set -euo pipefail
umask 077

directory="$HOME/.config/lia-fibra"
install -d -m 700 "$directory"
printf 'Chiave API OpenAI del tunnel (input nascosto): ' > /dev/tty
IFS= read -r -s key < /dev/tty
printf '\n' > /dev/tty
if [[ -z "$key" || "$key" == *[[:space:]]* ]]; then
    printf 'Chiave vuota o contenente spazi: nessuna modifica.\n' >&2
    exit 1
fi
temporary=$(mktemp "$directory/.tunnel-api-key.XXXXXX")
trap 'rm -f "$temporary"; unset key' EXIT
printf '%s' "$key" > "$temporary"
unset key
if [[ -f "$directory/tunnel-api-key" ]]; then
    cp -p "$directory/tunnel-api-key" "$directory/tunnel-api-key.backup.$(date -u +%Y%m%dT%H%M%SZ)"
fi
mv -f "$temporary" "$directory/tunnel-api-key"
systemctl --user restart lia-fibra-tunnel.service
printf 'Credenziale salvata privatamente. Avvio tunnel richiesto.\n'