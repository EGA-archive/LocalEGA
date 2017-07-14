# Local EGA implementation

This repo contains python code to start a _Local EGA_.

Python 3.6+ is required. The code has been tested against 3.6.1.

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
An example is provided in [main.yaml](../loggers/main.yaml) or [debug.yaml](../loggers/debug.yaml).

