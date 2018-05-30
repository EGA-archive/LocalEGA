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

pip3.6 install PyYaml Markdown aiohttp==2.3.8 aiohttp-jinja2==0.13.0

mkdir -p /var/lib/cega/users
unzip -d /var/lib/cega/users /tmp/cega_users.zip
systemctl start cega-users.service
systemctl enable cega-users.service

# RabbitMQ
yum -y install rabbitmq-server
echo '[rabbitmq_management].' > /etc/rabbitmq/enabled_plugins
cat > /etc/rabbitmq/rabbitmq.config <<EOF
%% -*- mode: erlang -*-
%%
[%% {rabbit,[{loopback_users, [ ] },
 %% 	  {default_vhost, "/"},
 %% 	  {default_user,  "guest"},
 %%	  {default_pass,  "guest"},
 %%	  {default_permissions, [".*", ".*",".*"]},
 %%	  {default_user_tags, [administrator]},
 %%	  {disk_free_limit, "1GB"}]},
 {rabbitmq_management, [ {load_definitions, "/etc/rabbitmq/defs.json"} ]}
].
EOF
systemctl start rabbitmq-server
systemctl enable rabbitmq-server
