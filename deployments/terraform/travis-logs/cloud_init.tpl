#cloud-config
write_files:
  - encoding: b64
    content: ${boot}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'

runcmd:
  - /root/boot.sh ${kibana_passwd}

final_message: "The system is finally up, after $UPTIME seconds"

