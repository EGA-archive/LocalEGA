#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0


# ========================
# Postgres setup

psql -v ON_ERROR_STOP=1 -U postgres <<-EOSQL
ALTER USER postgres WITH password '${db_password}';
EOSQL

psql -v ON_ERROR_STOP=1 -U postgres -f /tmp/db.sql
