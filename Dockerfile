FROM alpine:latest
RUN apk add --no-cache python3 npm curl chromium openconnect git py3-pip uv socat

# Agent-browser.
RUN npm install -g agent-browser

# Openconnect-saml.
RUN mkdir -p /app
RUN cd /tmp \
  && git clone https://github.com/derkarnold/openconnect-saml.git \
  && cd openconnect-saml \
  && uv build \
  && cp dist/*.whl /app \
  && cd .. && rm -rf openconnect-saml

WORKDIR /app
RUN uv venv && uv pip install *.whl && rm *.whl
COPY ./auth_scripts/* .
COPY ./entrypoint.sh .
COPY ./port_forwards.sh .

ENTRYPOINT ./entrypoint.sh
