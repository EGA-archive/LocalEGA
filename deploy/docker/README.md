This document helps you prepare the (mininum) settings for your LocalEGA instance.

All files are encrypted using Crypt4GH.
The master key should be stored securely.

It requires:
* a service key
* a master key
* a configuration file for the python handler: `lega.ini`
* a configuration file for docker-compose: `docker-compose.yml`
* 2 configurations file for postgres: `pg.conf` and `pg_hba.conf`

We assume you have created a local user and a group named `lega`. If not, you can do it with

    groupadd -r lega
    useradd -M -g lega lega

Create the docker image (for ingestion) with:

	make image

Update the configuration files with the proper settings.
> Hint: copy the supplied sample files and adjust the passwords appropriately.

The included message broker uses an administrator account with
`admin:secret` as `username:password`. This is up to you to update it
in your production environment.

Generate the service key with:

	ssh-keygen -t ed25519 -f service.key -C "service_key@LocalEGA"
	chown lega service.key
	chown lega service.key.pub

Note: You will get prompted for the passphrase. Save it and update
`lega.ini` accordingly, with the proper filepath and the chosen
passphrase. (it is _not_ recommended _not to use_ any passphrase).

Repeat the same for the master key:

	ssh-keygen -t ed25519 -f master.key -C "master_key@LocalEGA"
	chown lega master.key
	chown lega master.key.pub
	

Finally, you need to prepare the storage mountpoints for:
* the inbox of the users
* staging area
* the vault location
* the backup location

```bash
	# Create the directories (some with the setgid bit)
	mkdir -p data/{inbox,staging,vault,vault.bkp}

	chown lega:lega data/inbox
	chmod 2750 data/inbox # with the setgid bit, the `lega` user can _read_ the inbox files of each user.
	                      # Other users then the owner can't.

	chown lega data/staging
	chmod 700 data/staging

	chown lega data/vault
	chmod 700 data/vault

	chown lega data/vault.bkp
	chmod 700 data/vault.bkp
```
Adjust the paths in the `docker-compose.yml` file and the `lega.ini` handler configuration.
