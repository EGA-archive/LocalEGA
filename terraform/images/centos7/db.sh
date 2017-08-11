yum -y update

yum -y install https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm

yum -y install postgresql96-server postgresql96-contrib

/usr/pgsql-9.6/bin/postgresql96-setup initdb
systemctl enable postgresql-9.6.service


mv /var/lib/pgsql/9.6/data/postgresql.conf /var/lib/pgsql/9.6/data/postgresql.conf.old
grep -v '^$\|^\s*\#' /var/lib/pgsql/9.6/data/postgresql.conf.old > /var/lib/pgsql/9.6/data/postgresql.conf
echo "listen_addresses = '*'" >> /var/lib/pgsql/9.6/data/postgresql.conf

mv /var/lib/pgsql/9.6/data/pg_hba.conf /var/lib/pgsql/9.6/data/pg_hba.conf.old
grep -v '^$\|^\s*\#' /var/lib/pgsql/9.6/data/pg_hba.conf.old > /var/lib/pgsql/9.6/data/pg_hba.conf
sed -i -e "s/local\(.*\)peer/local\1trust/" /var/lib/pgsql/9.6/data/pg_hba.conf
sed -i -e "s;host.*1/128.*ident;host all all all md5;" /var/lib/pgsql/9.6/data/pg_hba.conf

systemctl start postgresql-9.6.service



