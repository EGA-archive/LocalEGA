#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# semanage port -a -t syslogd_port_t -p tcp 10514

cat > /etc/rsyslog.d/ega.conf <<'EOF'
# for UDP use:
module(load="imudp") # needs to be done just once 
input(type="imudp" port="10514")
#$ModLoad imudp
#$InputUDPServerRun 10514

local1.* /var/log/ega.log
EOF

systemctl restart rsyslog

echo "EGA Monitoring ready"
