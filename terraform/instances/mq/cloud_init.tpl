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
    permissions: '0400'


runcmd:
  - systemctl start rabbitmq-server
  - rabbitmq-plugins enable rabbitmq_management
  - systemctl enable rabbitmq-server


final_message: "The system is finally up, after $UPTIME seconds"
