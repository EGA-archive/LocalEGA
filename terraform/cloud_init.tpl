#cloud-config
write_files:
  - encoding: b64
    content: ${base64encode(${boot_script})}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'
  - encoding: b64
    content: ${base64encode(${host_file})}
    owner: root:root
    path: /etc/hosts
    permissions: '0644'

runcmd:
  - /root/boot.sh
