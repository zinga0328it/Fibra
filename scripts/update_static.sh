#!/usr/bin/env bash
set -euo pipefail

# Script to sync static assets into a destination folder (default: /var/www/fibra).
# Usage:
#   DST=/path/to/dst ./scripts/update_static.sh   # copy into DST without requiring args
#   ./scripts/update_static.sh /path/to/dst --dry-run
#
# The script will attempt to run chown/chmod only if it runs as root.
SRC="/home/aaa/fibra/web/publica/"
DST="/var/www/fibra/"

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    shift
fi
if [[ -n "$1" ]]; then
    DST="$1"
fi
if [[ -n "${DST:-}" && -n "$DST" ]]; then
    : # already set
fi
if [[ -n "${DST:-}" && -z "$DST" ]]; then
    DST="/var/www/fibra/"
fi

# If the DST was provided through env var, use it
if [[ -n "${DST}" ]]; then
    :
fi

# If not root but DST is a system path, warn and exit; allow non-root for local testing
if [[ $(id -u) -ne 0 ]]; then
    if [[ "$DST" =~ ^/var/www ]]; then
        echo "Not running as root: cannot write to $DST. Use sudo or select a local destination (DST=/tmp/fibra)." >&2
        exit 1
    fi
fi

# Rsync static files only and ensure ownership and permissions are correct
# Rsync static files only and ensure ownership and permissions are correct
if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY RUN] rsync -av --delete ${SRC} ${DST}"
    rsync -av --delete --dry-run "${SRC}" "${DST}"
else
    rsync -av --delete "${SRC}" "${DST}"
    # Only attempt to chown/chmod if running as root
    if [[ $(id -u) -eq 0 ]]; then
        chown -R www-data:www-data "${DST}"
        find "${DST}" -type d -exec chmod 755 {} +
        find "${DST}" -type f -exec chmod 644 {} +
    else
        echo "Not root: skipping chown/chmod. Ensure permissions manually if needed."
    fi
fi

# Report
echo "Static assets synchronized to ${DST}."
if [[ $(id -u) -eq 0 ]]; then
    echo "Ownership and permissions adjusted to www-data:www-data"
else
    echo "You ran this as non-root; ownership/permissions may need adjusting" >&2
fi
exit 0
