# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=..
	CONF=<your-conf.ini-file>
	INBOX=<folder> # mapped to /home on the ega-inbox
	STAGING=<folder> # mapped to /ega/staging on the ega-workers
	VAULT=<folder> # mapped to /ega/vault on the ega-vault and ega-verify>
	RSA_HOME=<folder> # mapped to /root/.rsa on the ega-workers
	GPG_PUBRING=<gpg-pubring> # mapped to /root/.gnupg/pubring.kbx on the ega-gpg-agent and ega-workers
	

Moreover, some of the containers need extra variables. There are located in:
* `.env.d/gpg.env` with
```
PASSPHRASE=<something-complex>
```
* `.env.d/db.env`
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```
* `.env.d/inbox.env`
```
SSH_KEY=<your-key-to-login-onto-the-sftp-server>
```

## Running

	docker-compose up -d
	
If the images are not created, they will be. It takes some time.

## Stopping

	docker-compose down

## (re)build the images

	docker-compose build
