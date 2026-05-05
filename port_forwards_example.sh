#!/bin/sh

# Put your changes in here and rename this file to port_forwards.sh.
socat TCP-LISTEN:3389,fork,reuseaddr TCP:WINDOWSBOX:3389 &
socat UDP-LISTEN:3389,fork,reuseaddr UDP:WINDOWSBOX:3389 &

wait
