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
  - encoding: b64
    content: ${conf}
    owner: ega:ega
    path: /home/ega/.lega/conf.ini
    permissions: '0600'
  - encoding: b64
    content: ${gpg_public}
    owner: ega:ega
    path: /tmp/gpg_public.zip
    permissions: '0600'
  - encoding: b64
    content: ${gpg_private}
    owner: ega:ega
    path: /tmp/gpg_private.zip
    permissions: '0600'
  - encoding: b64
    content: ${certs_public}
    owner: ega:ega
    path: /tmp/certs_public.zip
    permissions: '0600'
  - encoding: b64
    content: ${certs_private}
    owner: ega:ega
    path: /tmp/certs_private.zip
    permissions: '0600'
  - encoding: b64
    content: ${rsa_public}
    owner: ega:ega
    path: /tmp/rsa_public.zip
    permissions: '0600'
  - encoding: b64
    content: ${rsa_private}
    owner: ega:ega
    path: /tmp/rsa_private.zip
    permissions: '0600'
  - encoding: b64
    content: ${gpg_passphrase}
    owner: ega:ega
    path: /tmp/gpg_passphrase
    permissions: '0600'
  - encoding: b64
    content: ${ega_service}
    owner: root:root
    path: /etc/systemd/system/ega-socket-proxy.service
    permissions: '0750'

runcmd:
  - su -c "/home/ega/boot.sh" - ega

final_message: "The system is finally up, after $UPTIME seconds"
