# Local EGA implementation

This repo contains python code to start a _Local EGA_.

LocalEGA comprises several components: worker(s), vault-listener, verification-step, connectors to CentralEGA, error-monitors, an sftp-inbox and a frontend.

You can install LocalEGA as follows:

	pip install PyYaml Mardown
	pip install -e <ega-folder>
	
Apart from the frontend, all the other components can be started multiple times.

## Configuration and Logging settings

Most of the LocalEGA components can be started with configuration and logging command-line arguments.

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from the package's `defaults.ini`
* from a local untracked `~/.lega/conf.ini`
* and finally from the file specified as the `--conf` argument.

Note: No need to update the `defaults.ini`. Instead, to reset any
key/value pairs, either update `~/.lega/conf.ini` or create your own
file passed to `--conf` as a command-line arguments.

The necessary configuration settings are:
* ...

## Logging

The `--log <file>` argument is used to configuration where the logs go.
Without it, we look at the `DEFAULT/log_conf` key/value pair from the loaded configuration.
If the latter doesn't exist, there is no logging capabilities.

The `<file>` can be in `INI` or `YAML` format.
An example is provided in [main.yaml](./logs/main.yaml) or [debug.yaml](./logs/debug.yaml).

## Prior to running the Local EGA components

It is necessary to have the following, already running:
* a gpg-agent (with the `--homedir` properly set)
* a message broker, and
* a postgres database

We provide scripts in the [tools folder](./tools) as suggestions to start the above components.

For the **database**, use `./tools/start_db.sh` which boots a docker container, and sets up the appropriate tables.
		
For the **message broker**, use `./tools/start_mq.sh` which boots a docker container with RabbitMQ and its management plugin.
Note: it also configures the broker's exchange, the queues and the bindings.

Finally, the **gpg-agent** can be started ahead of time as using `./tools/start_agent.sh`.
The script kills any other gpg-agent and boots a new one (version 2.0), with the passphrase preset for the EGA gpg-key.
You should not forget to source the created `[GNUPGHOME]/agent.env` so that the workers find the gpg-agent.
Note: This will be unnecessary with version `2.1`

## A simple alternative

An alternative to running the above scripts is to use the script
`tools/start_ega.sh`. It starts the necessary components of Local EGA:
It connects (a fake) CentralEGA to LocalEGA, for both file ingestion
and user account creation; it starts the frontend, the other
components including 2 workers (which know how to contact the
pre-configured gpg-agent).

A trap is added so that `Ctrl-C` kills all the background processes that
the script started.


