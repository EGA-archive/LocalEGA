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
    content: ${ega_ssh_keys}
    owner: root:ega
    path: /usr/local/bin/ega-ssh-keys.sh
    permissions: '0750'

bootcmd:
  - mkdir -p /usr/local/lib/ega

runcmd:
  - yum -y install automake autoconf libtool libgcrypt libgcrypt-devel postgresql-devel pam-devel libcurl-devel jq-devel nfs-utils
  - echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
  - git clone https://github.com/NBISweden/LocalEGA-auth.git ~/repo && cd ~/repo/src && make install && ldconfig -v
  - /root/boot.sh ${cidr}


final_message: "The system is finally up, after $UPTIME seconds"
