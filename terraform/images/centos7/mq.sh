yum -y update
yum -y install http://download.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-10.noarch.rpm
yum -y install erlang
yum -y install https://github.com/rabbitmq/rabbitmq-server/releases/download/rabbitmq_v3_6_10/rabbitmq-server-3.6.10-1.el7.noarch.rpm

# copy rabbitmq.config to /etc/rabbitmq/rabbitmq.config
# copy rabbitmq.json to /etc/rabbitmq/defs.json

systemctl enable rabbitmq-server
systemctl start rabbitmq-server

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management
