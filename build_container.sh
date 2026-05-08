#!/bin/sh

. "$(dirname "$0")/select_runtime.sh"
select_runtime "$1" || exit 1

echo "Using runtime: $RUNTIME"
$RUNTIME build . -t openconnect-saml-portforward
