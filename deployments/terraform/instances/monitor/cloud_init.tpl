#cloud-config
write_files:
  - encoding: b64
    content: ${hosts}
    owner: root:root
    path: /etc/hosts
    permissions: '0644'
  - encoding: b64
    content: ${hosts_allow}
    owner: root:root
    path: /etc/hosts.allow
    permissions: '0644'
  - encoding: b64
    content: ${users}
    owner: root:root
    path: /etc/nginx/ega_kibana_users
    permissions: '0644'
  - encoding: b64
    content: ${es}
    owner: root:root
    path: /etc/elasticsearch/elasticsearch.yml
    permissions: '0644'
  - encoding: b64
    content: ${kibana}
    owner: root:root
    path: /etc/kibana/kibana.yml
    permissions: '0644'
  - encoding: b64
    content: ${logstash}
    owner: root:root
    path: /etc/logstash/conf.d/10-logstash.conf
    permissions: '0644'

runcmd:
  - chown -R elasticsearch /usr/share/elasticsearch
  - systemctl start logstash elasticsearch kibana nginx
  - systemctl enable logstash elasticsearch kibana nginx

final_message: "The system is finally up, after $UPTIME seconds"
