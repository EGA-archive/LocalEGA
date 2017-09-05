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
After=user.slice systemd-logind.service

[Socket]
ListenStream=/home/ega/.gnupg/S.gpg-agent
SocketUser=ega
SocketGroup=ega
SocketMode=0600
ExecStartPre=/usr/bin/mkdir -m 500 /run/user/$(id -u ega)/gnupg
# It is a trick to fool the gnupg_socketdir function, so it defaults to homedir
Service=ega-gpg-agent.service

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/ega-gpg-agent.service <<EOF
[Unit]
Description=EGA GPG agent
After=syslog.target
After=network.target

Requires=ega-gpg-agent.socket
After=ega-gpg-agent.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStart=/usr/local/bin/gpg-agent --supervised
#ExecReload=/usr/local/bin/gpgconf --reload gpg-agent
RuntimeDirectory=ega

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

cat > /etc/systemd/system/ega-socket-proxy.service <<EOF
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
ExecStart=/bin/ega-socket-proxy 'ega-keys:9010' /home/ega/.gnupg/S.gpg-agent --certfile \$EGA_GPG_CERTFILE --keyfile \$EGA_GPG_KEYFILE
RuntimeDirectory=ega

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert
Environment=EGA_GPG_KEYFILE=~/.certs/selfsigned.key

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

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
#extra-socket /run/ega/gnupg/S.gpg-agent
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF
chown ega:ega ~ega/.gnupg/gpg-agent.conf
chmod 640 ~ega/.gnupg/gpg-agent.conf

##############
echo "Enable lingering for the ega user"
loginctl enable-linger ega
# So that /run/user/1001 does not get cleaned

echo "Starting the gpg-agent proxy"
systemctl start ega-socket-proxy.service ega-gpg-agent.service ega-gpg-agent.socket
systemctl enable ega-socket-proxy.service ega-gpg-agent.service ega-gpg-agent.socket
