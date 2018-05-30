#cloud-config
write_files:
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
    content: ${ega_ingest}
    owner: root:root
    path: /etc/systemd/system/ega-ingestion@.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_inbox_mount}
    owner: root:root
    path: /etc/systemd/system/ega-inbox.mount
    permissions: '0644'
  - encoding: b64
    content: ${ega_staging_mount}
    owner: root:root
    path: /etc/systemd/system/ega-staging.mount
    permissions: '0644'

bootcmd:
  - mkdir -p /ega
  - chown ega:ega /ega
  - chmod 700 /ega

runcmd:
  - pip3.6 uninstall -y lega
  - pip3.6 install pika==0.11.0 psycopg2==2.7.4 cryptography==2.1.4
  - pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@feature/pgp
  - systemctl start ega-ingestion@1.service ega-ingestion@2.service
  - systemctl enable ega-ingestion@1.service ega-ingestion@2.service

final_message: "The system is finally up, after $UPTIME seconds"
