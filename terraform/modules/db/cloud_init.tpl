#cloud-config
write_files:
  - encoding: b64
    content: ${db_sql}
    owner: postgres:postgres
    path: /tmp/db.sql
    permissions: '0644'
  - encoding: b64
    content: ${boot_script}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'

runcmd:
  - /root/boot.sh
