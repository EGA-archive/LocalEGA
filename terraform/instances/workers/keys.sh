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
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/.certs && chmod 700 ~/.certs
mkdir -p ~/.gnupg/private-keys-v1.d && chmod 700 ~/.gnupg/private-keys-v1.d

unzip /tmp/gpg.zip -d ~/.gnupg
unzip /tmp/gpg_private.zip -d ~/.gnupg/private-keys-v1.d
unzip /tmp/rsa.zip -d ~/.rsa
unzip /tmp/certs.zip -d ~/.certs

rm /tmp/gpg.zip
rm /tmp/gpg_private.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

chmod 600 ~/.gnupg/{pubring.kbx,trustdb.gpg}
chmod -R 700 ~/.gnupg/private-keys-v1.d
chmod 640 ~/.certs/*.cert
chmod 600 ~/.certs/*.key
chmod 640 ~/.rsa/ega-public.pem
chmod 600 ~/.rsa/ega.pem

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

cat > /etc/systemd/system/gpg-agent.socket <<EOF
[Unit]
Description=GPG-agent socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=/root/.gnupg/S.gpg-agent
FileDescriptorName=std
SocketMode=0600
DirectoryMode=0700
#Service=gpg-agent.service

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/gpg-agent-extra.socket <<EOF
[Unit]
Description=GPG-agent (limited) socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=/root/.gnupg/S.gpg-agent.extra
FileDescriptorName=extra
SocketMode=0600
DirectoryMode=0700
Service=gpg-agent.service

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/gpg-agent.service <<EOF
[Unit]
Description=GPG-agent
Documentation=man:gpg-agent(1)
After=syslog.target
After=network.target

Requires=gpg-agent.socket

[Service]
Slice=ega.slice
Type=simple
ExecStart=/usr/local/bin/gpg-agent --supervised
ExecReload=/usr/local/bin/gpgconf --reload gpg-agent
#ExecStop=/usr/bin/pkill gpg-agent
ExecPost=/root/preset.sh

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/ega-socket-proxy.service <<EOF
[Unit]
Description=EGA Socket Proxy service (GPG-master on port 9010)
After=syslog.target
After=network.target

Requires=gpg-agent.service
Requires=gpg-agent-extra.socket

[Service]
Slice=ega.slice
Type=simple
ExecStart=/bin/ega-socket-proxy 'ega-keys:9010' /root/.gnupg/S.gpg-agent.extra --certfile \$EGA_GPG_CERTFILE --keyfile \$EGA_GPG_KEYFILE

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

cat > ~/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
extra-socket /root/.gnupg/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF

##############
# echo "Enabling the ega user to linger"
# loginctl enable-linger ega

echo "Starting the gpg-agent proxy"
systemctl start gpg-agent.socket gpg-agent-extra.socket gpg-agent.service ega-socket-proxy.service
systemctl enable gpg-agent.socket gpg-agent-extra.socket gpg-agent.service ega-socket-proxy.service

echo "Master GPG-agent ready"
# echo "Rebooting"
# systemctl reboot
