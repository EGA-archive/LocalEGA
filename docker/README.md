# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=..
	CONF=<your-conf.ini-file>
	INBOX=<its-location>
	STAGING=<its-location>
	VAULT=<its-location>
	GPG_HOME=<its-location>
	RSA_HOME=<its-location>
	

Moreover, some of the containers need extra variables. There are located in:
* `.env.d/gpg.env` with
```
PASSPHRASE=<something-complex>
```
* .env.d/db.env
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```
* .env.d/inbox.env
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
