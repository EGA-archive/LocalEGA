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
  - encoding: b64
    content: ${mq_cega_defs}
    owner: rabbitmq:rabbitmq
    path: /etc/rabbitmq/defs-cega.json
    permissions: '0640'
  - encoding: b64
    content: ${mq_creds}
    owner: rabbitmq:rabbitmq
    path: /etc/rabbitmq/creds.rc
    permissions: '0600'
  - encoding: b64
    content: ${ega_slice}
    owner: root:root
    path: /etc/systemd/system/ega.slice
    permissions: '0644'
  - encoding: b64
    content: ${mq_load}
    owner: root:root
    path: /etc/systemd/system/ega-mq-cega-defs.service
    permissions: '0644'

runcmd:
  - rabbitmq-plugins enable --offline rabbitmq_management
  - rabbitmq-plugins enable --offline rabbitmq_federation
  - rabbitmq-plugins enable --offline rabbitmq_federation_management
  - rabbitmq-plugins enable --offline rabbitmq_shovel
  - rabbitmq-plugins enable --offline rabbitmq_shovel_management
  - systemctl start rabbitmq-server
  - systemctl enable rabbitmq-server
  - /root/mq_users.sh
  - systemctl start ega-mq-cega-defs.service
  - systemctl enable ega-mq-cega-defs.service

final_message: "The system is finally up, after $UPTIME seconds"
