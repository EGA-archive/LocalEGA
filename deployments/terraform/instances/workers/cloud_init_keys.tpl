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
    content: ${keys_conf}
    owner: ega:ega
    path: /etc/ega/keys.ini
    permissions: '0600'
  - encoding: b64
    content: ${ssl_cert}
    owner: ega:ega
    path: /etc/ega/ssl.cert
    permissions: '0600'
  - encoding: b64
    content: ${ssl_key}
    owner: ega:ega
    path: /etc/ega/ssl.key
    permissions: '0600'
  - encoding: b64
    content: ${rsa_pub}
    owner: ega:ega
    path: /etc/ega/rsa/ega.pub
    permissions: '0600'
  - encoding: b64
    content: ${rsa_sec}
    owner: ega:ega
    path: /etc/ega/rsa/ega.sec
    permissions: '0600'
  - encoding: b64
    content: ${pgp_pub}
    owner: ega:ega
    path: /etc/ega/pgp/ega.pub
    permissions: '0600'
  - encoding: b64
    content: ${pgp_sec}
    owner: ega:ega
    path: /etc/ega/pgp/ega.sec
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
    content: ${ega_keys}
    owner: root:root
    path: /etc/systemd/system/ega-keyserver.service
    permissions: '0644'
  - encoding: b64
    content: ${iptables}
    owner: root:root
    path: /etc/sysconfig/iptables
    permissions: '0600'

runcmd:
  - yum -y install nc nmap tcpdump iptables-services
  - systemctl start iptables.service
  - systemctl enable iptables.service
  - pip3.6 uninstall -y lega
  - pip3.6 install aiohttp==2.3.8 cryptography==2.1.3
  - pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@feature/pgp
  - systemctl start ega-keyserver.service
  - systemctl enable ega-keyserver.service


final_message: "The system is finally up, after $UPTIME seconds"
