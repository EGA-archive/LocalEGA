#!/bin/bash

set -euo pipefail

if [[ -z $1 ]]; then
	echo "Supply a hostname"
	exit 1
fi
host=$1
shift

timeout=${2:-60}

echo "connecting to $host"
ssh $@ $host "echo 'GPG agent tunnel active for $timeout seconds. Interrupt (^C) when finished.'; sleep $timeout"
