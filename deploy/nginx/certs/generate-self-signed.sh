#!/usr/bin/env sh
# Generate self-signed TLS certs for internal trial (replace with real certs in production).
set -eu

DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"

# The subject must escape the space in the organisation, or OpenSSL answers "subject name is expected to be
# in the format /type0=value0/..." and — because -keyout is written before the subject is validated — leaves
# a NEW private key beside the OLD certificate, which nginx then refuses to start with ("key values
# mismatch"). Generating into a temporary pair, checking that the two belong together, and only then moving
# both into place is what keeps a failed run from breaking a working directory.
SUBJECT="/CN=localhost/O=Zhenhang\ ERP/C=CN"

tmp_key="${DIR}/.privkey.pem.tmp"
tmp_crt="${DIR}/.fullchain.pem.tmp"
trap 'rm -f "${tmp_key}" "${tmp_crt}"' EXIT INT TERM

if command -v openssl >/dev/null 2>&1; then
  # MSYS (Git Bash) rewrites anything that looks like a POSIX path, so `/CN=localhost/...` reaches OpenSSL as
  # a Windows path and is rejected with "subject name is expected to be in the format /type0=value0/...". That
  # is what made this script fail here while its own docker fallback worked.
  #
  # Excluding the conversion wholesale then broke the file arguments, because the Windows OpenSSL cannot open
  # `/d/...`. So the conversion is excluded and the two paths are handed over in native form instead — via
  # `cygpath -w`, which only exists on MSYS.
  native() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi
  }

  MSYS2_ARG_CONV_EXCL='*' openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$(native "${tmp_key}")" -out "$(native "${tmp_crt}")" -subj "${SUBJECT}"
  key_modulus="$(openssl rsa -in "${tmp_key}" -noout -modulus)"
  crt_modulus="$(openssl x509 -in "${tmp_crt}" -noout -modulus)"
else
  docker run --rm -v "${DIR}:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /certs/.privkey.pem.tmp -out /certs/.fullchain.pem.tmp -subj "${SUBJECT}"
  key_modulus="$(docker run --rm -v "${DIR}:/certs" alpine/openssl rsa -in /certs/.privkey.pem.tmp -noout -modulus)"
  crt_modulus="$(docker run --rm -v "${DIR}:/certs" alpine/openssl x509 -in /certs/.fullchain.pem.tmp -noout -modulus)"
fi

if [ "${key_modulus}" != "${crt_modulus}" ]; then
  echo "ERROR: the generated key and certificate do not match; nothing was replaced." >&2
  exit 1
fi

mv "${tmp_key}" "${DIR}/privkey.pem"
mv "${tmp_crt}" "${DIR}/fullchain.pem"

echo "Wrote ${DIR}/fullchain.pem and ${DIR}/privkey.pem"
