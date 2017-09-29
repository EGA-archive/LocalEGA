# Local EGA implementation

This repo contains python code to start a _Local EGA_.

Python 3.6+ is required. The code has been tested against 3.6.1.

You can provision and deploy the different components:

* locally, using [docker-compose](../docker).
* on an OpenStack cluster, using [terraform](../terraform).
	

## Configuration and Logging settings

Most of the LocalEGA components can be started with configuration and logging command-line arguments.

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from the package's `defaults.ini`
* from the file `/etc/ega/conf.ini` (if it exists)
* and finally from the file specified as the `--conf` argument.

Note: No need to update the `defaults.ini`. Instead, to reset any
key/value pairs, either update `/etc/ega/conf.ini` or create your own
file passed to `--conf` as a command-line arguments.

## Logging

The `--log <file>` argument is used to configuration where the logs go.
Without it, we look at the `DEFAULT/log_conf` key/value pair from the loaded configuration.
If the latter doesn't exist, there is no logging capabilities.

The `<file>` argument can either be a file path in `INI` or `YAML`
format, or one of the following keywords: `default`, `debug` or
`syslog`. In the latter case, it uses some
default [logger files](lega/conf/loggers).
