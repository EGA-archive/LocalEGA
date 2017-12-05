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
    content: ${mq_defs}
    owner: rabbitmq:rabbitmq
    path: /etc/rabbitmq/defs.json
    permissions: '0600'
  - encoding: b64
    content: ${mq_conf}
    owner: rabbitmq:rabbitmq
    path: /etc/rabbitmq/rabbitmq.config
    permissions: '0600'
  - encoding: b64
    content: ${mq_users}
    owner: root:root
    path: /root/mq_users.sh
    permissions: '0700'


runcmd:
  - echo '[rabbitmq_management].' > /etc/rabbitmq/enabled_plugins
  - systemctl start rabbitmq-server
  - systemctl enable rabbitmq-server
  - /root/mq_users.sh

final_message: "The system is finally up, after $UPTIME seconds"
