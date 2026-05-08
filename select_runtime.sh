#!/bin/sh
# Source this file, then call: select_runtime [docker|podman] || exit 1
# Sets RUNTIME variable on success.

select_runtime() {
    if [ -n "$1" ]; then
        case "$1" in
            docker|podman)
                if ! command -v "$1" > /dev/null 2>&1; then
                    echo "Error: '$1' not found in PATH." >&2
                    AVAILABLE=""
                    command -v podman > /dev/null 2>&1 && AVAILABLE="podman"
                    command -v docker > /dev/null 2>&1 && AVAILABLE="${AVAILABLE:+$AVAILABLE, }docker"
                    if [ -n "$AVAILABLE" ]; then
                        echo "Available runtime(s): $AVAILABLE" >&2
                    else
                        echo "No container runtime found." >&2
                    fi
                    return 1
                fi
                RUNTIME="$1"
                ;;
            *) echo "Usage: $0 [docker|podman]" >&2; return 1 ;;
        esac
    elif command -v podman > /dev/null 2>&1; then
        RUNTIME="podman"
    elif command -v docker > /dev/null 2>&1; then
        RUNTIME="docker"
    else
        echo "Error: neither podman nor docker found in PATH" >&2
        return 1
    fi
}
