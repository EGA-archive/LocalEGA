#!/bin/bash

set -e

the_trap () {
  [[ -z "$INSTANCE" ]] && INST="anonymous" || INST=$INSTANCE
  if [[ -z "$2" ]]; then
    curl -d '{"instance":"'"$INST"'", "service":"lega-keyserver", "status": "'"$1"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  else
    curl -d '{"instance":"'"$INST"'", "service":"lega-keyserver", "status": "'"$1"'", "exitStatus" : "'"$2"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  fi
}

# KEYSERVER_PORT env must be defined
[[ -z "$KEYSERVER_PORT" ]] && echo 'Environment KEYSERVER_PORT is empty' 1>&2 && the_trap 'stopped' 1 && exit 1

the_trap 'started'

GPG=/usr/local/bin/gpg2
GPG_AGENT=/usr/local/bin/gpg-agent
GPG_PRESET=/usr/local/libexec/gpg-preset-passphrase

pkill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

# Start the GPG Agent in /root/.gnupg
${GPG_AGENT} --daemon
# This should create /run/ega/S.gpg-agent{,.extra,.ssh}

#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(${GPG} -k --with-keygrip ${GPG_EMAIL} | awk '/Keygrip/{print $3;exit;}')
${GPG_PRESET} --preset -P ${GPG_PASSPHRASE} ${KEYGRIP}
unset GPG_PASSPHRASE

echo "Starting the gpg-agent proxy"
ega-socket-proxy "0.0.0.0:${KEYSERVER_PORT}" /root/.gnupg/S.gpg-agent --certfile /etc/ega/ssl.cert --keyfile /etc/ega/ssl.key &

keyserver () {
  echo "Starting the key management server"
  ega-keyserver --keys /etc/ega/keys.ini
}

trap 'the_trap "stopped" $?' TERM INT
keyserver &
PID=$!
wait $PID
