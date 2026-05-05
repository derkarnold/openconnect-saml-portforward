#!/bin/sh

./port_forwards.sh &
sleep 1 && echo $VPN_PASSWORD | uv run openconnect-saml \
	--headless --server $VPN_SERVER --user $VPN_USERNAME \
  	--no-sudo --auth-script $VPN_AUTH_SCRIPT
