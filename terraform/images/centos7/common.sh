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

yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y update
yum -y install gcc git curl make bzip2 unzip patch \
               openssl openssh-server \
	       nss-tools nc nmap tcpdump lsof strace \
	       bash-completion bash-completion-extras \
	       python36u python36u-pip

mkdir -p /var/src/gnupg
(
    cd /var/src/gnupg
    # Copy the RPMS from git
    # libgpg-error libgcrypt libassuan libksba npth ncurses pinentry gnupg2
    for f in libgpg-error-1.27 libgcrypt-1.8.1 libassuan-2.4.3 libksba-1.3.5 npth-1.5 ncurses-6.0 pinentry-1.0.0 gnupg-2.2.2
    do
	curl -OL https://github.com/NBISweden/LocalEGA/raw/terraform/extras/rpmbuild/RPMS/x86_64/${f}-1.el7.centos.x86_64.rpm
	rpm -i ${f}-1.el7.centos.x86_64.rpm
    done
)

cat > /etc/ld.so.conf.d/gpg2.conf <<EOF
/usr/local/lib
/usr/local/lib64
EOF
ldconfig -v

#################################
# Python 3 missing stuff

[[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so
[[ -e /usr/local/bin/python3 ]]  || ln -s /bin/python3.6 /usr/local/bin/python3

# Installing required packages
pip3.6 install PyYaml Markdown pika aiohttp pycryptodomex aiopg colorama aiohttp-jinja2

##############################################################
# Create ega user (with default settings)
useradd -m ega

# Update cloud-init
sed -i -e "s/name:\scentos/name: ega/" /etc/cloud/cloud.cfg
sed -i -e "s/gecos:.*/gecos: EGA User/" /etc/cloud/cloud.cfg

# Note: Update the sudo rights?

# Turning it off
poweroff
