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
    content: ${conf}
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
    content: ${ega_verify}
    owner: root:root
    path: /etc/systemd/system/ega-verify.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_vault}
    owner: root:root
    path: /etc/systemd/system/ega-vault.service
    permissions: '0644'
  - encoding: b64
    content: ${ega_vault_mount}
    owner: root:root
    path: /etc/systemd/system/ega-vault.mount
    permissions: '0644'
  - encoding: b64
    content: ${ega_staging_mount}
    owner: root:root
    path: /etc/systemd/system/ega-staging.mount
    permissions: '0644'

bootcmd:
  - mkdir -p -m 0700 /ega
  - chown ega:ega /ega

runcmd:
  - mkfs -t btrfs -f /dev/vdb
  - systemctl start ega-verify ega-vault
  - systemctl enable ega-verify ega-vault

final_message: "The system is finally up, after $UPTIME seconds"
