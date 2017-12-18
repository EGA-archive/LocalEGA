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
    content: ${users}
    owner: root:root
    path: /etc/nginx/ega_kibana_users
    permissions: '0644'
    		 
final_message: "The system is finally up, after $UPTIME seconds"
