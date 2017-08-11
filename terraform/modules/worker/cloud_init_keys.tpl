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
  - encoding: gzip
    content: !!binary |
      ${gpg}
    owner: root:root
    path: /root/.gnupg
    permissions: '0755'
  - encoding: gzip
    content: !!binary |
      ${certs}
    owner: root:root
    path: /etc/ega
    permissions: '0755'
  - encoding: gzip
    content: !!binary |
      ${rsa}
    owner: root:root
    path: /root/.rsa
    permissions: '0755'

runcmd:
  - /root/boot.sh
