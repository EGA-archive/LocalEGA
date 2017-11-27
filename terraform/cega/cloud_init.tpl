#cloud-config
write_files:
  - encoding: b64
    content: ${mq_defs}
    owner: rabbitmq:rabbitmq
    path: /etc/rabbitmq/defs.json
    permissions: '0400'
  - encoding: b64
    content: ${cega_users}
    owner: root:root
    path: /tmp/cega_users.zip
    permissions: '0400'
  - encoding: b64
    content: ${cega_server}
    owner: root:root
    path: /var/lib/cega/server.py
    permissions: '0755'
  - encoding: b64
    content: ${cega_html}
    owner: root:root
    path: /var/lib/cega/users.html
    permissions: '0755'
  - encoding: b64
    content: ${cega_env}
    owner: root:root
    path: /var/lib/cega/env
    permissions: '0400'
  - encoding: b64
    content: ${ega_slice}
    owner: root:root
    path: /etc/systemd/system/ega.slice
    permissions: '0644'
  - encoding: b64
    content: ${ega_service}
    owner: root:root
    path: /etc/systemd/system/cega-users.service
    permissions: '0644'

bootcmd:
 - mkdir -p /var/lib/cega/users

runcmd:
  - unzip -d /var/lib/cega/users /tmp/cega_users.zip
  - systemctl start rabbitmq-server
  - rabbitmq-plugins enable rabbitmq_management
  - systemctl enable rabbitmq-server
  - systemctl start cega-users.service
  - systemctl enable cega-users.service


final_message: "The system is finally up, after $UPTIME seconds"
