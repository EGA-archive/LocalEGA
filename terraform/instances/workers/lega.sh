#!/bin/bash

set -e

mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/certs && chmod 700 ~/certs

unzip /tmp/gpg.zip -d ~/.gnupg
unzip /tmp/rsa.zip -d ~/.rsa
unzip /tmp/certs.zip -d ~/certs

rm /tmp/gpg.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

# echo "Waiting for Message Broker"
# until /bin/nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do /bin/sleep 1; done
# echo "Waiting for database"
# until /bin/nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do /bin/sleep 1; done
# echo "Waiting for GPG and SSH agent"
# until /bin/nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do /bin/sleep 1; done


EGA_SOCKET=$(gpgconf --list-dirs agent-socket) # we are the ega user

sudo tee -a /etc/systemd/system/ega-socket-forwarder.service >/dev/null <<EOF
[Unit]
Description=EGA Socket forwarding service (to GPG-master on port 9010)
After=syslog.target
After=network.target

[Service]
Type=simple
User=ega
Group=ega
ExecStartPre=-/bin/rm -f ${EGA_SOCKET}
ExecStart=/bin/ega-socket-forwarder ${EGA_SOCKET} '192.168.10.12:9010' --certfile \$EGA_GPG_CERTFILE

Environment=EGA_GPG_CERTFILE=~/certs/selfsigned.cert

[Install]
WantedBy=multi-user.target
EOF

echo "Starting the gpg-agent forwarder"
sudo systemctl start ega-socket-forwarder.service

echo "Starting the worker"
sudo systemctl start ega-worker.service

echo "Enabling services"
sudo systemctl enable ega-socket-forwarder.service
sudo systemctl enable ega-worker.service

echo "LEGA ready"
