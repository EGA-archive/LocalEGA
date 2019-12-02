Installation
============

.. highlight:: shell

The sources for LocalEGA can be downloaded and installed from the `NBIS Github repo`_.

.. code-block:: console

    $ pip install git+https://github.com/EGA-archive/LocalEGA.git

The recommended method is however to use one of our deployment
strategy: either on `Docker`_ or on `OpenStack cloud`_.

Configuration
=============

A few files are required in order to connect the different components.

The main configurations are set by default, and it is possible to
overwrite any of them. All Python components can indeed be started
using the ``--conf <file>`` switch to specify the configuration file.

The settings are loaded, in order:

* from environment variables (where the naming convention is uppercase ``section_option`` (as in ``default.ini``), e.g. ``ARCHIVE_STORAGE_DRIVER`` or ``POSTGRES_DB``,
* from the package's ``defaults.ini``,
* from the file ``/etc/ega/conf.ini`` (if it exists),
* and finally from the file specified as the ``--conf`` argument.

Therefore, there is no need to update the ``defaults.ini``. Instead,
reset/update any key/value pairs by creating a custom configuration file and pass it
to ``--conf`` as a command-line argument.

See a `full description of the environment variable settings
<https://github.com/NBISweden/LocalEGA/wiki/Configuration-Settings-%7C-Environment-Variables>`_.


Logging
=======

A similar mechanism is used to overwrite the default logging settings.

The ``--log <file>`` argument is used to configuration where the logs
go.  Without it, we look at the ``DEFAULT/log_conf`` key/value pair
from the loaded configuration.  If the latter doesn't exist, there is
no logging capabilities.

The ``<file>`` argument can either be a file path in ``INI`` or
``YAML`` format, or a *keyword*. In the latter case, the logging
mechanism will search for a log file, using that keyword, in the
`default loggers
<https://github.com/NBISweden/LocalEGA/tree/dev/lega/conf/loggers>`_. Currently,
``default``, ``debug``, ``console``, ``logstash`` and
``logstash-debug`` are available.

Using the `logstash logger
<https://github.com/NBISweden/LocalEGA/blob/dev/lega/conf/loggers/logstash-debug.yaml>`_,
we leverage the famous *ELK* stack, which stands for **E**\
lasticsearch, **L**\ ogstash and **K**\ ibana. Logstash receives the
logs. Elasticsearch stores them and make them searchable. Kibana
contacts the Elasticsearch service to display the logs in a web
interface.

.. image:: /static/Kibana.png
   :target: _static/Kibana.png
   :alt: Kibana


.. _NBIS Github repo: https://github.com/NBISweden/LocalEGA
.. _Docker: https://github.com/NBISweden/LocalEGA/tree/dev/docker
.. _OpenStack cloud: https://github.com/NBISweden/LocalEGA-deploy-terraform
