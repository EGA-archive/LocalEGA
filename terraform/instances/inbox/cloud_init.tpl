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

bootcmd:
  - mkdir -p /usr/local/lib/ega
  - rm -rf /ega
  - mkdir -m 0755 /ega
  - chown root:ega /ega
  - chmod g+s /ega

runcmd:
  - yum -y install automake autoconf libtool libgcrypt libgcrypt-devel postgresql-devel pam-devel libcurl-devel jq-devel nfs-utils
  - echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
  - mkfs -t btrfs -f /dev/vdb
  - echo '/dev/vdb /ega btrfs defaults 0 0' >> /etc/fstab
  - mount /ega
  - echo '/ega ${cidr}(rw,sync,no_root_squash,no_all_squash,no_subtree_check)' > /etc/exports
  - mkdir -m 0755 /ega/{inbox,staging}
  - chown root:ega /ega/{inbox,staging}
  - chmod g+s /ega/{inbox,staging}
  - systemctl restart rpcbind nfs-server nfs-lock nfs-idmap
  - systemctl enable rpcbind nfs-server nfs-lock nfs-idmap
  - git clone https://github.com/NBISweden/LocalEGA-auth.git ~/repo && cd ~/repo/src && make install && ldconfig -v
  - cp /etc/pam.d/sshd /etc/pam.d/sshd.bak
  - mv -f /etc/pam.d/ega_sshd /etc/pam.d/sshd
  - cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
  - sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf


final_message: "The system is finally up, after $UPTIME seconds"
