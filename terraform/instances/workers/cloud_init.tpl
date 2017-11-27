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
    content: ${hosts_allow}
    owner: root:root
    path: /etc/hosts.allow
    permissions: '0644'
  - encoding: b64
    content: ${lega_conf}
    owner: ega:ega
    path: /etc/ega/conf.ini
    permissions: '0600'
  - encoding: b64
    content: ${gpg_pubring}
    owner: ega:ega
    path: /ega/.gnupg/pubring.kbx
    permissions: '0600'
  - encoding: b64
    content: ${gpg_trustdb}
    owner: ega:ega
    path: /ega/.gnupg/trustdb.gpg
    permissions: '0600'
  - encoding: b64
    content: ${ssl_cert}
    owner: ega:ega
    path: /etc/ega/ssl.cert
    permissions: '0600'
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
    content: ${ega_socket}
    owner: root:root
    path: /etc/systemd/system/ega-socket-forwarder.socket
    permissions: '0644'
  - encoding: b64
    content: ${ega_forward}
    owner: root:root
    path: /etc/systemd/system/ega-socket-forwarder.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_ingest}
    owner: root:root
    path: /etc/systemd/system/ega-socket-ingestion.service
    permissions: '0644'

bootcmd:
  - mkdir -p -m 0700 /ega
  - chown -R ega:ega /ega
  - mkdir -p ~ega/.gnupg && chmod 700 ~ega/.gnupg

runcmd:
  - /root/boot.sh

final_message: "The system is finally up, after $UPTIME seconds"
