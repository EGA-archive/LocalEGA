#cloud-config
write_files:
  - encoding: b64
    content: ${boot_script}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'
  - encoding: b64
    content: ${hosts}
    owner: root:root
    path: /etc/hosts
    permissions: '0644'
  - encoding: b64
    content: ${conf}
    owner: ega:ega
    path: /etc/ega/conf.ini
    permissions: '0600'
  - encoding: b64
    content: ${gpg}
    owner: ega:ega
    path: /tmp/gpg.zip
    permissions: '0600'
  - encoding: b64
    content: ${certs}
    owner: ega:ega
    path: /tmp/certs.zip
    permissions: '0600'
  - encoding: b64
    content: ${rsa}
    owner: ega:ega
    path: /tmp/rsa.zip
    permissions: '0600'

runcmd:
  - /root/boot.sh

final_message: "The system is finally up, after $UPTIME seconds"
