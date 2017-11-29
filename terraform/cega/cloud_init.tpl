#cloud-config
write_files:
  - encoding: b64
    content: ${mq_defs}
    owner: root:root
    path: /etc/rabbitmq/defs.json
    permissions: '0644'
  - encoding: b64
    content: ${mq_conf}
    owner: root:root
    path: /etc/rabbitmq/rabbitmq.config
    permissions: '0644'
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
  - echo '[rabbitmq_management].' > /etc/rabbitmq/enabled_plugins
  - systemctl start rabbitmq-server
  - systemctl enable rabbitmq-server
  - unzip -d /var/lib/cega/users /tmp/cega_users.zip
  - systemctl start cega-users.service
  - systemctl enable cega-users.service


final_message: "The system is finally up, after $UPTIME seconds"
