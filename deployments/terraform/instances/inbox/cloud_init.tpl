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
    content: ${ega_mount}
    owner: root:root
    path: /etc/systemd/system/ega.mount
    permissions: '0644'

bootcmd:
  - mkdir -p /usr/local/lib/ega
  - rm -rf /ega
  - mkdir -m 0750 /ega

runcmd:
  - yum -y install automake autoconf libtool libgcrypt libgcrypt-devel postgresql-devel pam-devel libcurl-devel jq-devel nfs-utils fuse fuse-libs
  - echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
  - modprobe fuse
  - mkdir -p /mnt/fuse
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
  - git clone https://github.com/NBISweden/LocalEGA-auth.git ~/repo && cd ~/repo/src && make install && ldconfig -v
  - pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@dev
  - systemctl start ega-inbox.service
  - systemctl enable ega-inbox.service
  - cp /etc/pam.d/sshd /etc/pam.d/sshd.bak
  - mv -f /etc/pam.d/ega_sshd /etc/pam.d/sshd
  - cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
  - sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf


final_message: "The system is finally up, after $UPTIME seconds"
