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
    content: ${ega_service}
    owner: root:root
    path: /etc/systemd/system/ega-frontend.service
    permissions: '0644'

runcmd:
  - git clone https://github.com/NBISweden/LocalEGA.git ~/repo
  - pip3.6 install ~/repo/src
  - systemctl start ega-frontend
  - systemctl enable ega-frontend

final_message: "The system is finally up, after $UPTIME seconds"
