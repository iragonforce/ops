# Purpose:
# Preserve the CLI tools required by the Nexus Hermes agent
# across container recreation.
#
# Input:
# Pinned upstream Hermes v0.21.6 OCI image.
#
# Output:
# Hermes image with GitHub CLI, rsync, fd and wget.
#
# This image does not contain runtime configuration,
# SSH keys, credentials, workspace data or Docker access.

FROM nousresearch/hermes-agent:v0.21.6@sha256:55e192fba0cd4fde61142abbff5adeacff40efdb482ccd0ff877924bd274f909

USER root

RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      --no-install-recommends \
      gh \
      rsync \
      fd-find \
      wget; \
    if ! command -v fd >/dev/null 2>&1; then \
      ln -s /usr/bin/fdfind /usr/local/bin/fd; \
    fi; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    command -v gh; \
    command -v rsync; \
    command -v fd; \
    command -v wget
