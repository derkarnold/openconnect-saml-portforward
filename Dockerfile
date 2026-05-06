FROM alpine:latest
RUN apk add --no-cache python3 npm curl chromium openconnect git py3-pip uv socat

# Agent-browser.
RUN npm install -g agent-browser

RUN mkdir -p /app
WORKDIR /app
RUN uv venv && uv pip install openconnect-saml

COPY ./auth_scripts/* .
COPY ./entrypoint.sh .
COPY ./port_forwards.sh .

ENTRYPOINT ./entrypoint.sh
