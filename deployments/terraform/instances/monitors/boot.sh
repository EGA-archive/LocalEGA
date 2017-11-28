#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0


# ========================
# semanage port -a -t syslogd_port_t -p tcp 10514

echo "Restarting RSyslog to capture EGA logs"


cat > /etc/rsyslog.d/ega.conf <<'EOF'
# Module
$ModLoad imtcp

# Template: log every host in its own file
$template EGAlogs,"/var/log/ega/%HOSTNAME%.log"

# Remote Logging
$RuleSet EGARules
local1.* /var/log/ega-old.log
*.* ?EGAlogs

# bind ruleset to tcp listener
$InputTCPServerBindRuleset EGARules

# and activate it:
$InputTCPServerRun 10514
EOF

systemctl restart rsyslog

echo "EGA Monitoring ready"
