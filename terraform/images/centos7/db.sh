yum -y update

yum -y install https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm

yum -y install postgresql96-server postgresql96-contrib

/usr/pgsql-9.6/bin/postgresql96-setup initdb
systemctl enable postgresql-9.6.service

copy db.sql into /tmp/db.sql
chmod 666 /tmp/db.sql

systemctl start postgresql-9.6.service
su -s /bin/sh -c "psql -f /tmp/db.sql" postgres
