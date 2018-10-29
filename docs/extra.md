Configuration
-------------

A few files are required in order to connect the different components.

The main configurations are set by default, and it is possible to
overwrite any of them. All Python components can indeed be started
using the ``--conf <file>`` switch to specify the configuration file.

The settings are loaded, in order:

* from environment variables (where the naming convention is uppercase ``section_option`` (as in ``default.ini``), e.g. ``VAULT_DRIVER`` or ``POSTGRES_DB``,
* from the package's ``defaults.ini``,
* from the file ``/etc/ega/conf.ini`` (if it exists),
* and finally from the file specified as the ``--conf`` argument.

Therefore, there is no need to update the ``defaults.ini``. Instead,
reset/update any key/value pairs by creating a custom configuration file and pass it
to ``--conf`` as a command-line argument.

See a `full description of the environment variable settings
<https://github.com/NBISweden/LocalEGA/wiki/Configuration-Settings-%7C-Environment-Variables>`_.


Logging
-------

A similar mechanism is used to overwrite the default logging settings.

The ``--log <file>`` argument is used to configuration where the logs
go.  Without it, we look at the ``DEFAULT/log_conf`` key/value pair
from the loaded configuration.  If the latter doesn't exist, there is
no logging capabilities.

The ``<file>`` argument can either be a file path in ``INI`` or
``YAML`` format, or a *keyword*. In the latter case, the logging
mechanism will search for a log file, using that keyword, in the
`default loggers
<https://github.com/EGA-archive/LocalEGA/tree/master/lega/conf/loggers>`_. Currently,
``default``, ``debug``, ``console``, ``logstash`` and
``logstash-debug`` are available.

Using the `logstash logger
<https://github.com/EGA-archive/LocalEGA/blob/master/lega/conf/loggers/logstash-debug.yaml>`_,
we leverage the famous *ELK* stack, which stands for **E**\
lasticsearch, **L**\ ogstash and **K**\ ibana. Logstash receives the
logs. Elasticsearch stores them and make them searchable. Kibana
contacts the Elasticsearch service to display the logs in a web
interface.

.. image:: /static/Kibana.png
   :target: _static/Kibana.png
   :alt: Kibana
