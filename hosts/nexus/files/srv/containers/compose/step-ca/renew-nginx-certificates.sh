#!/bin/sh
# Renew the existing local Nginx TLS certificates using the maintained CA workflow. See renew-nginx-homelab.sh(1) for source and integration details.
if [ "${1-}" = '--help' ] && [ "$#" -eq 1 ]; then
  cat <<'OPS_USAGE_TEXT'
Renew the existing local Nginx TLS certificates using the maintained CA workflow.
Usage: renew-nginx-homelab.sh  [ARGUMENT ...]

Source: hosts/nexus/files/srv/containers/compose/step-ca/renew-nginx-certificates.sh in ~/ops
See man renew-nginx-homelab.sh for the existing call sites and argument handling.
OPS_USAGE_TEXT
  exit 0
fi
# Renew only certificates already issued to local NPM hosts; never initialize a CA.
set -eu
DATA=/srv/containers/data/nginx/data/homelab-stepca
ROOT=/srv/containers/data/step-ca/export
INTERMEDIATE=/srv/containers/data/step-ca/certs/intermediate_ca.crt
changed=0
for name in paperclip hermes nexus; do
    dir="$DATA/$name"
    [ -f "$dir/leaf.crt" ] || continue
    before=$(sha256sum "$dir/leaf.crt" | cut -d' ' -f1)
    docker run --rm --network host --add-host=ca.homelab.lan:192.168.1.2 --user 0:0 --entrypoint step \
      -v "$DATA:/out" -v "$ROOT:/ca:ro" \
      smallstep/step-ca:0.30.2@sha256:a2b17872915c193259b75a5474c398326f41bd199f0842093e52cf4182bc8270 ca renew "/out/$name/leaf.crt" "/out/$name/privkey.pem" \
      --ca-url https://ca.homelab.lan:9000 --root /ca/root_ca.crt \
      --expires-in=18h --force
    after=$(sha256sum "$dir/leaf.crt" | cut -d' ' -f1)
    if [ "$before" != "$after" ]; then
        python3 - "$dir" "$INTERMEDIATE" <<'PY'
from pathlib import Path
import os
import sys
p = Path(sys.argv[1])
intermediate = Path(sys.argv[2])
tmp = p / 'fullchain.pem.new'
tmp.write_bytes((p / 'leaf.crt').read_bytes() + intermediate.read_bytes())
os.chown(tmp, 568, 568)
os.chmod(tmp, 0o600)
os.replace(tmp, p / 'fullchain.pem')
PY
        chown 568:568 "$dir/leaf.crt" "$dir/privkey.pem"
        chmod 600 "$dir/leaf.crt" "$dir/privkey.pem"
        changed=1
    fi
done
if [ "$changed" -eq 1 ]; then
    docker exec nginx-proxy-manager nginx -t
    docker exec nginx-proxy-manager nginx -s reload
fi
