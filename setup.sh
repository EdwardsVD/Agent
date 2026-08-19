#!/usr/bin/env bash
# Forwarding to install.sh
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install.sh" "$@"
