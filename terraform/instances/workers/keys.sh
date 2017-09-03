#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

##############
# Public + Private parts
mkdir -p ~ega/.gnupg && chmod 700 ~ega/.gnupg
mkdir -p ~ega/.rsa && chmod 700 ~ega/.rsa
mkdir -p ~ega/.certs && chmod 700 ~ega/.certs
mkdir -p ~ega/.gnupg/private-keys-v1.d && chmod 700 ~ega/.gnupg/private-keys-v1.d

unzip /tmp/gpg.zip -d ~ega/.gnupg
unzip /tmp/gpg_private.zip -d ~ega/.gnupg/private-keys-v1.d
unzip /tmp/rsa.zip -d ~ega/.rsa
unzip /tmp/certs.zip -d ~ega/.certs

rm /tmp/gpg.zip
rm /tmp/gpg_private.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

chown -R ega:ega ~ega/.gnupg
chown -R ega:ega ~ega/.rsa
chown -R ega:ega ~ega/.certs

chmod 600 ~ega/.gnupg/{pubring.kbx,trustdb.gpg}
chmod -R 700 ~ega/.gnupg/private-keys-v1.d
chmod 640 ~ega/.certs/*.cert
chmod 600 ~ega/.certs/*.key
chmod 640 ~ega/.rsa/ega-public.pem
chmod 600 ~ega/.rsa/ega.pem

##############
git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

##############
#EGA_SOCKET=$(su -c "gpgconf --list-dirs agent-extra-socket" - ega) # as ega user

cat > /etc/systemd/system/ega.slice <<EOF
[Unit]
Description=EGA Slice
DefaultDependencies=no
Before=slices.target

#[Slice]
#CPUShares=512
#MemoryLimit=2G
EOF

cat > /etc/systemd/system/ega-gpg-agent.socket <<EOF
[Unit]
Description=GPG-agent socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=/run/ega/S.gpg-agent
SocketUser=ega
SocketGroup=ega
SocketMode=0600
DirectoryMode=0755

Service=ega-gpg-agent.service

[Install]
WantedBy=sockets.target
EOF

# To be run as EGA user
cat > /usr/local/bin/ega_create_socket_link.sh <<'EOF'
#!/bin/bash
[[ $# -ne 1 ]] && echo "Specify one argument (only): Bailing out..." && exit 1
EGA_GPG_SOCKET=$(gpgconf --list-dirs $1-socket)
[[ -z "$EGA_GPG_SOCKET" ]] && echo "We couldn't find the gpg socket location: Bailing out..." && exit 2
[[ -f "$EGA_GPG_SOCKET" ]] && echo "GPG socket link already in $EGA_GPG_SOCKET" && exit 0
# otherwise, create the file
mkdir -p $(dirname $EGA_GPG_SOCKET)
cat > $EGA_GPG_SOCKET <<EOFSOCKET
%Assuan%
socket=/run/ega/$(basename $EGA_GPG_SOCKET)
EOFSOCKET
#chown ega:ega $EGA_GPG_SOCKET
chmod 600 $EGA_GPG_SOCKET
echo "GPG socket link created (see $EGA_GPG_SOCKET)"
EOF
chown ega:ega /usr/local/bin/ega_create_socket_link.sh
chmod 700 /usr/local/bin/ega_create_socket_link.sh

cat > /etc/systemd/system/ega-gpg-agent.service <<EOF
[Unit]
Description=EGA GPG agent
After=syslog.target
After=network.target

Requires=ega-gpg-agent.socket
After=ega-gpg-agent.socket

# For the runtime directory to be correctly set
After=systemd-logind.service
After=user@$(id -u ega).service

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStartPre=/usr/local/bin/ega_create_socket_link.sh agent
ExecStart=/usr/local/bin/gpg-agent --supervised
#ExecReload=/usr/local/bin/gpgconf --reload gpg-agent
PermissionsStartOnly=false

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-gpg-agent.socket

[Install]
WantedBy=multi-user.target
RequiredBy=ega-socket-proxy.service
EOF

cat > /etc/systemd/system/ega-socket-proxy.service <<'EOF'
[Unit]
Description=EGA Socket Proxy service (GPG-master on port 9010)
After=syslog.target
After=network.target

Requires=ega-gpg-agent.service
After=ega-gpg-agent.service

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStart=/bin/ega-socket-proxy 'ega-keys:9010' /run/ega/S.gpg-agent --certfile $EGA_GPG_CERTFILE --keyfile $EGA_GPG_KEYFILE

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert
Environment=EGA_GPG_KEYFILE=~/.certs/selfsigned.key

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

#ConditionPathExists=/run/ega/S.gpg-agent
#ConditionPathExists=/run/user/1001/gnupg/S.gpg-agent

[Install]
WantedBy=multi-user.target
EOF

cat > ~ega/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
#extra-socket /run/ega/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF
chown ega:ega ~ega/.gnupg/gpg-agent.conf
chmod 640 ~ega/.gnupg/gpg-agent.conf

##############
echo "Starting the gpg-agent proxy"
systemctl start ega-socket-proxy.service ega-gpg-agent.service ega-gpg-agent.socket
systemctl enable ega-socket-proxy.service ega-gpg-agent.service ega-gpg-agent.socket
