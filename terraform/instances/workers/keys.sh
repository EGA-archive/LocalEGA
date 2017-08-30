#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sudo sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sudo sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
sudo setenforce 0


##############
# Public + Private parts
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/certs && chmod 700 ~/certs
mkdir -p ~/.gnupg/private-keys-v1.d && chmod 700 ~/.gnupg/private-keys-v1.d

unzip /tmp/gpg.zip -d ~/.gnupg
unzip /tmp/gpg_private.zip -d ~/.gnupg/private-keys-v1.d
unzip /tmp/rsa.zip -d ~/.rsa
unzip /tmp/certs.zip -d ~/certs

rm /tmp/gpg.zip
rm /tmp/gpg_private.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

chmod 600 ~/.gnupg/{pubring.kbx,trustdb.gpg}
chmod 700 ~/.gnupg/private-keys-v1.d
chmod 700 ~/.gnupg/private-keys-v1.d/*
chmod 640 ~/certs/*.cert
chmod 600 ~/certs/*.key
chmod 640 ~/certs/*.cert
chmod 600 ~/.rsa/ega.pem
chmod 640 ~/.rsa/ega-public.pem

##############
git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

##############
EGA_SOCKET=$(gpgconf --list-dirs agent-extra-socket) # we are the ega user

sudo tee -a /etc/systemd/system/ega-socket-proxy.service >/dev/null <<EOF
[Unit]
Description=EGA Socket Proxy service (port 9010)
After=syslog.target
After=network.target

[Service]
Type=simple
User=ega
Group=ega
ExecStartPre=-/usr/bin/pkill gpg-agent
ExecStartPre=-/bin/rm -f $EGA_SOCKET
ExecStartPre=/usr/local/bin/gpg-agent --daemon
ExecStart=/bin/ega-socket-proxy '192.168.10.12:9010' $EGA_SOCKET --certfile \$EGA_GPG_CERTFILE --keyfile \$EGA_GPG_KEYFILE
ExecStop=-/bin/rm -f $EGA_SOCKET

Environment=EGA_GPG_CERTFILE=~/certs/selfsigned.cert
Environment=EGA_GPG_KEYFILE=~/certs/selfsigned.key

StandardOutput=syslog
StandardError=syslog

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
extra-socket $EGA_SOCKET
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF
chmod 640 ~/.gnupg/gpg-agent.conf

##############
echo "Starting the gpg-agent proxy"
sudo systemctl start ega-socket-proxy.service
sudo systemctl enable ega-socket-proxy.service

##############
#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg2 -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
if [ ! -z "$KEYGRIP" ]; then 
    echo 'Unlocking the GPG key'
    /usr/local/libexec/gpg-preset-passphrase --preset -P "$(cat /tmp/gpg_passphrase)" $KEYGRIP && \
	rm -f /tmp/gpg_passphrase
else
    echo 'Skipping the GPG key preseting'
fi

echo "Master GPG-agent ready"
