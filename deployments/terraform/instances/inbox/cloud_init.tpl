#cloud-config
write_files:
  - encoding: b64
    content: ${hosts}
    owner: root:root
    path: /etc/hosts
    permissions: '0700'
  - encoding: b64
    content: ${conf}
    owner: root:root
    path: /etc/ega/conf.ini
    permissions: '0644'
  - encoding: b64
    content: ${auth_conf}
    owner: root:root
    path: /etc/ega/auth.conf
    permissions: '0644'
  - encoding: b64
    content: ${boot_script}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'
  - encoding: b64
    content: ${ega_mount}
    owner: root:root
    path: /etc/systemd/system/ega.mount
    permissions: '0644'
  - encoding: b64
    content: ${ega_inbox}
    owner: root:root
    path: /etc/systemd/system/ega-inbox.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_options}
    owner: root:root
    path: /etc/ega/options
    permissions: '0644'
  - encoding: b64
    content: ${ega_slice}
    owner: root:root
    path: /etc/systemd/system/ega.slice
    permissions: '0644'
  - encoding: b64
    content: ${ega_banner}
    owner: root:root
    path: /etc/banner
    permissions: '0644'

bootcmd:
  - mkdir -p /usr/local/lib/ega
  - rm -rf /ega
  - mkdir -m 0750 /ega

runcmd:
  - /root/boot.sh ${cidr}




final_message: "The system is finally up, after $UPTIME seconds"
