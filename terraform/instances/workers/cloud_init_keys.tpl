#cloud-config
write_files:
  - encoding: b64
    content: ${preset_script}
    owner: root:root
    path: /root/preset.sh
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
    content: ${keys_conf}
    owner: ega:ega
    path: /etc/ega/keys.ini
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
    content: ${gpg_private}
    owner: ega:ega
    path: /tmp/gpg_private.zip
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
    path: /etc/ega/rsa/pub.pem
    permissions: '0600'
  - encoding: b64
    content: ${rsa_sec}
    owner: ega:ega
    path: /etc/ega/rsa/sec.pem
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
    content: ${ega_proxy}
    owner: root:root
    path: /etc/systemd/system/ega-socket-proxy.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_keys}
    owner: root:root
    path: /etc/systemd/system/ega-keyserver.service
    permissions: '0644'
  - encoding: b64
    content: ${gpg_agent}
    owner: root:root
    path: /home/ega/.gnupg/gpg-agent.conf
    permissions: '0644'
  - encoding: b64
    content: ${gpg_agent_service}
    owner: root:root
    path: /etc/systemd/system/gpg-agent.service
    permissions: '0644'
  - encoding: b64
    content: ${gpg_agent_socket}
    owner: root:root
    path: /etc/systemd/system/gpg-agent.socket
    permissions: '0644'
  - encoding: b64
    content: ${gpg_agent_extra}
    owner: root:root
    path: /etc/systemd/system/gpg-agent-extra.socket
    permissions: '0644'

bootcmd:
  - mkdir -p ~ega/.gnupg && chmod 700 ~ega/.gnupg
  - mkdir -p ~ega/.gnupg/private-keys-v1.d && chmod 700 ~ega/.gnupg/private-keys-v1.d
  - unzip /tmp/gpg_private.zip -d ~ega/.gnupg/private-keys-v1.d
  - rm /tmp/gpg_private.zip
  - ldconfig -v
  - pip3.6 install git+https://github.com/NBISweden/LocalEGA.git
  - systemctl start gpg-agent.socket gpg-agent-extra.socket gpg-agent.service ega-socket-proxy.service ega-keyserver.service
  - systemctl enable gpg-agent.socket gpg-agent-extra.socket gpg-agent.service ega-socket-proxy.service ega-keyserver.service


final_message: "The system is finally up, after $UPTIME seconds"
