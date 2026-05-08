#!/bin/sh

# Put your changes in here and rename this file to port_forwards.sh.
WINDOWSPC=SOMEPC.SOMEDOMAN.com
socat TCP-LISTEN:3389,fork,reuseaddr TCP:$WINDOWSPC:3389 &
socat UDP-LISTEN:3389,fork,reuseaddr UDP:$WINDOWSPC:3389 &

wait
