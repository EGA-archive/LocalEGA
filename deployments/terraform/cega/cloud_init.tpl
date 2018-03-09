#cloud-config
write_files:
  - encoding: b64
    content: ${mq_users}
    owner: root:root
    path: /root/mq_users.sh
    permissions: '0700'
  - encoding: b64
    content: ${mq_defs}
    owner: root:root
    path: /etc/rabbitmq/defs.json
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
    content: ${cega_publish}
    owner: root:root
    path: /var/lib/cega/publish
    permissions: '0755'
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
  - encoding: b64
    content: ${ega_cert}
    owner: root:root
    path: /var/lib/cega/cega.cert
    permissions: '0644'
  - encoding: b64
    content: ${ega_cert_key}
    owner: root:root
    path: /var/lib/cega/cega.key
    permissions: '0644'
  - encoding: b64
    content: ${boot_script}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'

runcmd:
  - /root/boot.sh
  - /root/mq_users.sh

final_message: "The system is finally up, after $UPTIME seconds"
