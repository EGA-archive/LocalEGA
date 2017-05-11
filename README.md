# Local EGA implementation _using Python_

This repo contains python code to start a _Local EGA_.

There are 3 main components: ingestion, worker, vault

The ingestion, worker and vault modules can be respectively started as "_agents_" with:
* `python -m lega.ingestion --conf <file> --log <file>`
* `python -m lega.worker --conf <file> --log <file>`
* `python -m lega.vault --conf <file> --log <file>`

Several worker and vault _agents_ can be started.

The ingestion _agent_ start an asyncio web-server.

## Configuration

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from the package's `defaults.ini`
* from `~/.lega/conf.ini`
* and finally from the file specified as the `--conf` argument.

Note: No need to update the `defaults.ini`. Instead, to reset any
key/value pairs, either update `~/.lega/conf.ini` or create your own
file passed to `--conf` as a command-line arguments.

## Logging

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.
The `<file>` can be in `INI` or `YAML` format.
An example is provided in [log.yaml](./tools/log.yaml).

## Prior to running the Local EGA components

It is necessary to have the following, already running:
* a gpg-agent (with the `--homedir` properly set)
* a message broker, and
* a postgres database

We provide scripts in the [tools folder](./tools) as suggestions to start the above components.
Rename the `*.sh.sample` files into their corresponding `*.sh` and update the sensitive data in them.

For the **database**, use `./tools/start_db.sh` which boots a docker container.
		
For the **message broker**, use `./tools/start_mq.sh` which boots a docker container with RabbitMQ and its management plugin.
Note: it also configures the broker's exchange, the 3 queues, and the bindings.

Finally, the **gpg-agent** can be started ahead of time as using `./tools/start_agent.sh`.
The script kills any other gpg-agent and boots a new one (version 2.0), with the passphrase preset for the EGA gpg-key.
You should not forget to source the created `[GNUPGHOME]/agent.env` so that the workers find the gpg-agent.
Note: This will be unnecessary with version `2.1`

We also start another particular component: the fake *file-namer*, to
pose as CentralEGA. It is supposed to return a stable id which we'll
use as the name for a file in the vault. This component is started
with `python namer.py` (with `--log <file> --conf <file>` if
necessary). It uses a file called `namer.counter` in the same folder
as the script, which contains a number.

## Alternative

The script `tools/start_ega.sh` can be used to start the necessary
components of Local EGA.  It starts the ingestion frontend, 2 workers,
the vault listener, a file 'namer' that acts as the CentralEGA
instance. The gpg-agent is also started and the 2 workers source the
env file first.

A trap is added so that `Ctrl-C` kills all the background processes that
the script started.
