#!/bin/sh

podman run -it --rm --env-file .env -p 3389:3389 --privileged openconnect-saml-docker
