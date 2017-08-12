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
    owner: root:root
    path: /root/.lega/conf.ini
    permissions: '0600'
  - encoding: b64
    content: ${gpg}
    owner: root:root
    path: /tmp/gpg.zip
    permissions: '0600'
  - encoding: b64
    content: ${certs}
    owner: root:root
    path: /tmp/certs.zip
    permissions: '0600'
  - encoding: b64
    content: ${rsa}
    owner: root:root
    path: /tmp/rsa.zip
    permissions: '0600'
  - encoding: b64
    content: ${gpg_passphrase}
    owner: root:root
    path: /tmp/gpg_passphrase
    permissions: '0600'

runcmd:
  - /root/boot.sh

final_message: "The system is finally up, after $UPTIME seconds"
