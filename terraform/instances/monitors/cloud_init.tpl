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
    content: ${syslog_conf}
    owner: root:root
    path: /etc/rsyslog.d/ega.conf
    permissions: '0644'

runcmd:
  - systemctl restart rsyslog

final_message: "The system is finally up, after $UPTIME seconds"
