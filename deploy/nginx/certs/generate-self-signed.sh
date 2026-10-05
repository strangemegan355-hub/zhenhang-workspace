#!/usr/bin/env sh
# Generate self-signed TLS certs for internal trial (replace with real certs in production).
set -eu

DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"

if command -v openssl >/dev/null 2>&1; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${DIR}/privkey.pem" \
    -out "${DIR}/fullchain.pem" \
    -subj "/CN=localhost/O=Zhenhang ERP/C=CN"
else
  docker run --rm -v "${DIR}:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /certs/privkey.pem \
    -out /certs/fullchain.pem \
    -subj "/CN=localhost/O=Zhenhang ERP/C=CN"
fi

echo "Wrote ${DIR}/fullchain.pem and ${DIR}/privkey.pem"
