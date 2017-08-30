#cloud-config
write_files:
  - encoding: b64
    content: ${boot_script}
    owner: ega:ega
    path: /home/ega/boot.sh
    permissions: '0700'
  - encoding: b64
    content: ${hosts}
    owner: root:root
    path: /etc/hosts
    permissions: '0644'

runcmd:
  - su -c "/home/ega/boot.sh" - ega

final_message: "The system is finally up, after $UPTIME seconds"
