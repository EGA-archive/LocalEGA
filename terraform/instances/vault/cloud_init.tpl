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

runcmd:
  - mkfs -t btrfs /dev/vdb
  - mkdir -p -m 0700 /ega/vault
  - chown -R ega:ega /ega/vault
  - mount /dev/vdb /ega/vault
  - echo '/dev/vdb /ega/vault btrfs defaults 0 0' >> /etc/fstab
  - su -c "/home/ega/boot.sh" - ega

final_message: "The system is finally up, after $UPTIME seconds"
