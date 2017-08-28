#cloud-config
write_files:
  - encoding: b64
    content: ${boot_script}
    owner: root:root
    path: /root/boot.sh
    permissions: '0700'
  - encoding: b64
    content: ${lega_script}
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
  - encoding: b64
    content: ${ega_service_forwarder}
    owner: root:root
    path: /etc/systemd/system/ega-socket-forwarder.service
    permissions: '0750'
  - encoding: b64
    content: ${ega_service_worker}
    owner: root:root
    path: /etc/systemd/system/ega-worker.service
    permissions: '0750'

runcmd:
  - /root/boot.sh
  - su -c "/home/ega/boot.sh" - ega

final_message: "The system is finally up, after $UPTIME seconds"
