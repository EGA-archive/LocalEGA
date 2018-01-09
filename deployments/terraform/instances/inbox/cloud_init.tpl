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
    owner: root:root
    path: /etc/ega/conf.ini
    permissions: '0644'
  - encoding: b64
    content: ${auth_conf}
    owner: root:root
    path: /etc/ega/auth.conf
    permissions: '0644'
  - encoding: b64
    content: ${sshd_config}
    owner: root:root
    path: /etc/ssh/sshd_config
    permissions: '0644'
  - encoding: b64
    content: ${ega_pam}
    owner: root:root
    path: /etc/pam.d/ega
    permissions: '0644'
  - encoding: b64
    content: ${sshd_pam}
    owner: root:root
    path: /etc/pam.d/ega_sshd
    permissions: '0644'
  - encoding: b64
    content: ${ega_ssh_keys}
    owner: root:ega
    path: /usr/local/bin/ega-ssh-keys.sh
    permissions: '0750'
  - encoding: b64
    content: ${ega_ssh_keys}
    owner: root:ega
    path: /usr/local/bin/ega-ssh-keys.sh
    permissions: '0750'
  - encoding: b64
    content: ${fuse_cleanup}
    owner: root:ega
    path: /usr/local/bin/fuse_cleanup.sh
    permissions: '0750'
  - encoding: b64
    content: ${ega_mount}
    owner: root:root
    path: /etc/systemd/system/ega.mount
    permissions: '0644'

bootcmd:
  - mkdir -p /usr/local/lib/ega
  - rm -rf /ega
  - mkdir -m 0750 /ega

runcmd:
  - yum -y install automake autoconf libtool libgcrypt libgcrypt-devel postgresql-devel pam-devel libcurl-devel jq-devel nfs-utils fuse fuse-libs cronie
  - echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
  - modprobe fuse
  - mkdir -p /mnt/lega
  - mkfs -t btrfs -f /dev/vdb
  - systemctl start ega.mount
  - systemctl enable ega.mount
  - mkdir -p /ega/{inbox,staging}
  - chown root:ega /ega/inbox
  - chown ega:ega /ega/staging
  - chmod 0750 /ega/{inbox,staging}
  - chmod g+s /ega/{inbox,staging}
  - echo '/ega/inbox   ${cidr}(rw,sync,no_root_squash,no_all_squash,no_subtree_check)' > /etc/exports
  - echo '/ega/staging ${cidr}(rw,sync,no_root_squash,no_all_squash,no_subtree_check)' >> /etc/exports
  - systemctl restart rpcbind nfs-server nfs-lock nfs-idmap
  - systemctl enable rpcbind nfs-server nfs-lock nfs-idmap
  - git clone -b fuse https://github.com/NBISweden/LocalEGA-auth.git ~/repo && cd ~/repo/src && make install && ldconfig -v
  - pip3.6 uninstall -y lega
  - pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@feature/inbox-fuse
  - cp /etc/pam.d/sshd /etc/pam.d/sshd.bak
  - mv -f /etc/pam.d/ega_sshd /etc/pam.d/sshd
  - cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
  - sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf
  - echo '*/5 * * * * root /usr/local/bin/fuse_cleanup.sh /lega' >> /etc/crontab
  - systemctl start crond.service
  - systemctl enable crond.service




final_message: "The system is finally up, after $UPTIME seconds"
