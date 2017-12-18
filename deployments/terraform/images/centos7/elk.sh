#!/usr/bin/env bash

set -e # stop on errors
set -x # show me the commands

# ========================
# No IPv6
cat > /etc/sysctl.d/01-no-ipv6.conf <<EOF
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
cat > /etc/sysctl.d/02-swappiness.conf <<EOF
vm.swappiness = 1
EOF

# ========================
# Disable swap files
swapoff -a
# https://www.elastic.co/guide/en/elasticsearch/reference/current/setup-configuration-memory.html

# ========================

rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
yum -y install epel-release
yum -y update
yum -y install curl wget nginx httpd-tools unzip iptables-services

(
    cd ~
    wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2Ftechnetwork%2Fjava%2Fjavase%2Fdownloads%2Fjdk8-downloads-2133151.html; oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u152-b16/aa0333dd3019491ca4f6ddbe78cdb6d0/jdk-8u152-linux-x64.rpm
    yum -y localinstall jdk-8u152-linux-x64.rpm
)

# mkdir -p /usr/share/{kibana,elasticsearch,logstash}/config
# mkdir -p /usr/share/logstash/pipeline
# mkdir -p /etc/nginx/conf.d

cat > /etc/yum.repos.d/elk.repo <<'EOF'
[elasticsearch-6.x]
name=Elasticsearch repository for 6.x packages
baseurl=https://artifacts.elastic.co/packages/6.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md

[kibana-6.x]
name=Kibana repository for 6.x packages
baseurl=https://artifacts.elastic.co/packages/6.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md

[logstash-6.x]
name=Elastic repository for 6.x packages
baseurl=https://artifacts.elastic.co/packages/6.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF

yum -y install logstash elasticsearch kibana

cat > /etc/elasticsearch/elasticsearch.yml <<EOF
cluster.name: ega-monitor
network.host: 0.0.0.0
http.port: 9200
EOF

# Fix
chown -R elasticsearch /usr/share/elasticsearch

# cat > /etc/kibana/kibana.yml <<EOF
# server.port: 5601
# server.host: "localhost"
# elasticsearch.url: "http://localhost:9200"
# EOF

cat > /etc/logstash/conf.d/10-logstash.conf <<EOF
input {
      beats {
      	    port => 5600
      }
}
output {
	elasticsearch {
		hosts => ["localhost:9200"]
	}
}
EOF

# For NGINX

cat > /etc/nginx/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;


    server {
        listen 80;

    	#server_name travis-logs.ega.se;
	server_name _;

	auth_basic "Restricted Access";
    	auth_basic_user_file /etc/nginx/ega_kibana_users;

    	location / {
        	 proxy_pass http://localhost:5601;
        	 proxy_http_version 1.1;
	         proxy_set_header Upgrade $http_upgrade;
	         proxy_set_header Connection 'upgrade';
	         proxy_set_header Host $host;
	         proxy_cache_bypass $http_upgrade;        
    	}

	location = /40x.html {
	 	error_page 404 /usr/share/nginx/html/404.html;
        }

	location = /50x.html {
	        error_page 500 502 503 504 /usr/share/nginx/html/50x.html;
        }
    }

    # server {
    #     listen       80 default_server;
    #     listen       [::]:80 default_server;
    #     server_name  _;
    #     root         /usr/share/nginx/html;

    #     # Load configuration files for the default server block.
    #     include /etc/nginx/default.d/*.conf;

    #     location / {
    #     }

    #     error_page 404 /404.html;
    #         location = /40x.html {
    #     }

    #     error_page 500 502 503 504 /50x.html;
    #         location = /50x.html {
    #     }
    # }
}
EOF


# For SElinux
setsebool -P httpd_can_network_connect 1

# Start the services
systemctl daemon-reload
systemctl start logstash elasticsearch kibana nginx
systemctl enable logstash elasticsearch kibana nginx


# Iptables
cat > /etc/sysconfig/iptables <<EOF
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 5600 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF

systemctl start iptables
systemctl enable iptables

# Turning it off
#poweroff
