# Deploy LocalEGA using Docker


## Preliminary settings

Before you use the bootstrap script, it is required that the
connection to Central EGA already be created, along with a few other settings.

Create the following file in `bootstrap/settings.rc` and fill in the
following key/values pairs:


| Key | Value | Example | Description |
|-----|-------|---------|-------------|
| `DOCKER_PORT_inbox` | integer  | 2222 | Port mapping to access the container from the host or external network |
| `DOCKER_PORT_outgest` | integer  | 10443 | Port mapping to access the container from the host or external network |
| `CEGA_REST_PASSWORD` | string |  | Password to connect to the Central EGA Users ReST endpoint |
| `CEGA_CONNECTION` | string | amqps://&lt;user&gt;:&lt;password&gt;@hellgate.crg.eu:5271/&lt;vhost&gt; | CentralEGA [RabbitMQ URI](https://www.rabbitmq.com/uri-spec.html) |
| `LEGA_MQ_PASSWORD` | string | `$(generate_password 16)` | Password for the Local MQ broker admin user |
| `SSL_SUBJ` | string | `/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=SysDevs/CN=LocalEGA/emailAddress=all.ega@crg.eu` | Used to create the self-signed certificates |
| `EC_KEY_COMMENT` | string | LocalEGA@CRG | For the elliptic key, used by Crypt4GH |
| `EC_KEY_PASSPHRASE` | string | `$(generate_password 16)` | |
| `EC_KEY_COMMENT` | string | LocalEGA-signing@CRG | |
| `EC_KEY_PASSPHRASE` | string | `$(generate_password 16)` | |
| `DB_LEGA_IN_PASSWORD` | string | `$(generate_password 16)` | Password for the `lega_in` database user |
| `DB_LEGA_OUT_PASSWORD` | string | `$(generate_password 16)` | Password for the `lega_out` database user |
| `S3_ACCESS_KEY` | string | `$(generate_password 16)` | Access key for the S3 storage |
| `S3_SECRET_KEY` | string | `$(generate_password 32)` | Secret key for the S3 storage |



`generate_password` is provided in the [defs.sh](./bootstrap/defs.sh)
file and produces a random password of the given length (or 16 by
default).

## Bootstrap

You can then [generate the private data](bootstrap):

	make bootstrap
	# or
	make bootstrap-dev
	# for dummy passwords

The command will create a `.env` file and a `private` folder holding
the necessary data (ie the encryption keys, some passwords and
certificates for internal communication, etc... including the list of
microservices to boot).

The passwords are in `private/.trace` and the errors (if any) are in `private/.err`.

## Convenient commands

| Action   | Command          |
|----------|------------------|
| Running  | `make up`        |
| Stopping | `make down`      |
| Status   | `make ps`        |
| Delete   | `make clean-all` |
| Help     | `make help`      |

## Docker images

docker-compose will pull the appropriate images from [docker hub](https://hub.docker.com/u/egarchive/).
However, if you prefer, you can [create the EGA docker images](images), locally, with

	make -C images


## Logging

A simple logging mechanism is built in. Use the following command in
this directory, to see the logs in a terminal.

	docker-compose logs -f <service>

You can update the bootstrapped configuration file to use a different
logger (for eg Logstash, async, files, or a more verbose debug mode).

You can specify your own logger too. By default, we show the full debug output.

---

Note that, in this architecture, we use separate volumes, e.g. for
the inbox area, for the vault (here backed by S3). They
will be created on-the-fly by docker-compose.
