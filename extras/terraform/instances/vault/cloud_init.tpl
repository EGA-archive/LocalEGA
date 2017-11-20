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
    owner: ega:ega
    path: /etc/ega/conf.ini
    permissions: '0600'

runcmd:
  - mkfs -t btrfs -f /dev/vdb
  - rm -rf /ega/vault
  - mkdir -p /ega/vault
  - echo '/dev/vdb /ega/vault btrfs defaults 0 0' >> /etc/fstab
  - mount /ega/vault
  - chown ega:ega /ega/vault
  - chmod 0700 /ega/vault
  - /root/boot.sh

final_message: "The system is finally up, after $UPTIME seconds"
