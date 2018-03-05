# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# ========================
# No IPv6
cat > /etc/sysctl.d/01-no-ipv6.conf <<EOF
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF

# ========================

#yum -y update
yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y install python36u python36u-pip unzip

[[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so
[[ -e /usr/local/bin/python3 ]]  || ln -s /bin/python3.6 /usr/local/bin/python3

pip3.6 install PyYaml Markdown aiohttp aiohttp-jinja2

mkdir -p /var/lib/cega/users
unzip -d /var/lib/cega/users /tmp/cega_users.zip
systemctl start cega-users.service
systemctl enable cega-users.service
