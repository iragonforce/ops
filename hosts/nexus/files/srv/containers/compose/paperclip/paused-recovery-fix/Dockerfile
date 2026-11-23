ARG BASE_IMAGE
FROM ${BASE_IMAGE}
COPY --chown=node:node heartbeat.ts /app/server/src/services/heartbeat.ts
COPY --chown=node:node heartbeat.js /app/server/dist/services/heartbeat.js
