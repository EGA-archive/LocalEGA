#cloud-config
write_files:
  - encoding: b64
    content: ${db_sql}
    owner: postgres:postgres
    path: /tmp/db.sql
    permissions: '0600'
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

runcmd:
  - sed -i -e "s;host.*1/128.*ident;host all all ${cidr} md5;" /var/lib/pgsql/9.6/data/pg_hba.conf
  - systemctl start postgresql-9.6.service
  - systemctl enable postgresql-9.6.service
  - psql -v ON_ERROR_STOP=1 -U postgres -f /tmp/db.sql
  - rm -f /tmp/db.sql

final_message: "The system is finally up, after $UPTIME seconds"
