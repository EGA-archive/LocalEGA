# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to also create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=<python/code/folder>    # path to folder where setup.py is
	CONF=<path/to/your/ini/file> # will be mounted in the containers as /etc/ega/conf.ini
	
	RSA_HOME=<folder>         # mapped to /root/.rsa on the ega-workers
	GPG_HOME=<folder>         # Used on the agent-forwarder and the workers


The folder referenced by `GPG_HOME` should contain the following:

| Components | Used for... |
|----------:|------------|
| `pubring.kbx` | Access to the public ring by the workers and the gpg-agent master |
| `trustdb.gpg` | idem |
| `openpgp-revocs.d/` | Revoking keys. Only on the gpg-agent master |
| `private-keys-v1.d/`| idem |
| `certs/selfsigned.{cert,key}` | ... ssl encryption of the traffic between the workers and the gpg-agent master |

These files are created in advance by GPG (version 2.1+).

Moreover, some of the containers need extra variables. There are located in:
* `.env.d/gpg` with
```
GPG_PASSPHRASE=<something-complex>
```
* `.env.d/db`
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```

## Running

	docker-compose up -d
	
If the images are not created, they will be. <br/>
However, it is advised to [create them](images) beforehand.

Use `docker-compose up -d --scale worker=3` instead, if you want to start 3 workers.

Note that, in this architecture, we use 3 separate volumes: one for
the inbox area, one for the staging area, and one for the vault. They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down

## Status

	docker-compose ps

## Example

<a href="https://asciinema.org/a/nhHCuLd7mYjL4UgKQDI7uRJHs">
<img src="https://asciinema.org/a/nhHCuLd7mYjL4UgKQDI7uRJHs.png" width="836" style="display:block;margin:0 auto;"/>
</a>

	1) docker-compose up -d

We now create a "user" message in the broker. For that, we use the frontend and ega-publisher.

	2) docker-compose exec frontend ega-publisher inbox --broker 'cega.broker' --routing 'sweden.user' 'test' 'ssh-pub-key' 'some-hash'

We upload an encrypted file (here named data1)

	3) sftp -P 2222 test@localhost
	sftp> put <absolute/or/relative/path/to/file/named/data1>
	
Finally, we create a "file" message, again using the frontend.
	
	4) docker-compose exec frontend ega-publisher ingestion --broker 'cega.broker' --routing 'sweden.file' --enc "<bla>" --enc_algo 'md5' --unenc "<bla...>" --unenc_algo 'md5' test data1

Check now that the vault has the file and the message broker sent a message back in the CentralEGA queue, named `sweden.v1.commands.completed`.
