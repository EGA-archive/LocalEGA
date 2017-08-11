#cloud-config
write_files:
  - encoding: b64
    content: ${rabbitmq_config}
    owner: root:root
    path: /etc/rabbitmq/rabbitmq.config
    permissions: '0644'
  - encoding: b64
    content: ${rabbitmq_defs}
    owner: root:root
    path: /etc/rabbitmq/defs.json
    permissions: '0644'

runcmd:
  - systemctl enable rabbitmq-server
  - systemctl start rabbitmq-server
  - rabbitmq-plugins enable rabbitmq_management

final_message: "The system is finally up, after $UPTIME seconds"
