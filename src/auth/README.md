An NSS module to find the EGA users in a (remote) database

# Compile the library

	make

# Add it to the system

	make install

	echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
	
	ldconfig -v

`ldconfig` recreates the ld cache and also creates some extra links. (important!).

It is necessary to create `/etc/ega/auth.conf`. Use `auth.conf.sample` as an example.

# Make the system use it

Update `/etc/nsswitch.conf` and add the ega module first, for passwd

	passwd: files ega ...

Note: Don't put it first, otherwise it'll search for every users on the system (for ex: sshd).

# How it is build

This repository contains the NSS and PAM module for LocalEGA.

We use NSS to find out about the users, and PAM to authenticate them
(and check if the account has expired).

When the system needs to know about a specific user, it looks at its
`passwd` database. About you see that it first looks at its local
files (ie `/etc/passwd`) and then, if the user is not found, it looks
at the "ega" NSS module.

The NSS EGA module proceed in several steps:

* If the user is found a database,
  it is returned immediately. The database acts as a cache. Note that
  this database might be remote.

* If the user is not found in the database, we query CentralEGA (with
  a REST call). If the user doesn't exist there, it's the end of the
  journey.

* If the user exists at CentralEGA, we parse the JSON answer (at the
  moment a pair: `(password_hash, public_key)`) and put the retrieved
  user in the database. We then query the database again, and create
  the user's home directory (which location might vary per LocalEGA
  site).
  
* Upon new requests, only the database gets queried.

 The database credentials and queries are all configured in
`/etc/ega/auth.conf`. Note that we added a database trigger: When any
user is added, the expired ones are removed. We default to one month
after the last accessed date (See below for the PAM session).

Now that the user is retrieved, the PAM module takes the relay baton.

There are 4 components:

* `auth` is used to challenge the user credentials. We access the
  database only, and retrieve the user's password hash, which we
  compare to what the user inputs.

* `account` is used to check if the account has expired.

* `password` is used to re-create passwords. In our case, we don't
  need it so that component is left unimplemented.

* `session` is used whenever a user passes the authentication step and
  is about the log onto the service (in our case: sshd). When a
  session is open, we refresh the last access date of the user in the
  database.


# Configuration file sample

Place the following content in the file `/etc/ega/auth.conf` (or update the `#defile
CFGFILE` in [config.h](config.h))

```
debug = yes

##################
# Databases
##################
db_connection = host=<EGA_DB_IP> port=5432 dbname=lega user=<POSTGRES_USER> password=<POSTGRES_PASSWORD> connect_timeout=1 sslmode=disable

enable_rest = yes
rest_endpoint = http://cega_users/user/%s

##################
# NSS Queries
##################
nss_get_user = SELECT elixir_id,'x',<uid>,<gid>,'EGA User','/ega/inbox/'|| elixir_id,'/sbin/nologin' FROM users WHERE elixir_id = $1 LIMIT 1
nss_add_user = SELECT insert_user($1,$2,$3)

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = $1 LIMIT 1
pam_acct = SELECT elixir_id FROM users WHERE elixir_id = $1 and current_timestamp < last_accessed + expiration
pam_prompt = wazzzaaa: 
```
