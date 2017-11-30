#!/usr/bin/env bash

set -e # stop on errors
set -x # show me the commands

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# ========================

yum -y update
yum -y install epel-release
yum -y install gcc git curl make bzip2 unzip \
               openssl openssh-server rabbitmq-server \
	       nss-tools nc nmap tcpdump lsof strace \
	       bash-completion bash-completion-extras

yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y install python36u python36u-pip

[[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so
[[ -e /usr/local/bin/python3 ]]  || ln -s /bin/python3.6 /usr/local/bin/python3

pip3.6 install PyYaml Markdown pika aiohttp aiopg colorama aiohttp-jinja2

# Turning it off
poweroff
