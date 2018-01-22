Installation
============

.. highlight:: shell

The sources for LocalEGA can be downloaded and installed from the `NBIS Github repo`_.

.. code-block:: console

    $ pip install git+https://github.com/NBISweden/LocalEGA.git

The preferred method is however to use one of our deployment strategy: either on `Docker`_ or on `OpenStack cloud`_. 

Configuration
=============

A few files are required in order to connect the different components.

The main configurations are set by default, and it is possible to
overwrite any of them. All Python components can indeed be started
using the ``--conf <file>`` switch to specify the configuration file.

The settings are loaded, in order:

* from the package's ``defaults.ini``
* from the file ``/etc/ega/conf.ini`` (if it exists)
* and finally from the file specified as the ``--conf`` argument.

Therefore, there is no need to update the ``defaults.ini``. Instead,
reset/update any key/value pairs by creating your own file and pass it
to ``--conf`` as a command-line argument.


Logging
=======

A similar mechanism is used to overwrite the default logging settings.

The ``--log <file>`` argument is used to configuration where the logs go.
Without it, we look at the ``DEFAULT/log_conf`` key/value pair from the loaded configuration.
If the latter doesn't exist, there is no logging capabilities.

The ``<file>`` argument can either be a file path in ``INI`` or ``YAML``
format, or *keyword*. In the latter case, the logging mechanism will search for a log file, using that keyword, in the default loggers.

Currently, ``default``, ``debug``, ``syslog``, ``logstash`` and
``logstash-debug`` are `available`_.

Using the logstash logger, We leverage the famous *ELK* stack. *ELK*
stands for **E**\ lasticsearch, **L**\ ogstash and **K**\
ibana. Logstash receives the logs. Elasticsearch stores them and make
them searchable. Kibana contacts the Elasticsearch service to display
the logs in a web interface.


Bootstrap
=========

In order to simplify the setup of LocalEGA's components, we have
developped a few bootstrap scripts (one for the `Docker`_ deployment
and one for the `OpenStack cloud`_ deployment).

Those script create random passwords, configuration files, GnuPG keys,
RSA keys and connect the different components togehter.

All interesting settings are found the respective ``private``
directory of the LocalEGA instance. Look especially at the ``.trace``
file there.


.. _NBIS Github repo: https://github.com/NBISweden/LocalEGA
.. _Docker: https://github.com/NBISweden/LocalEGA/tree/dev/deployments/docker
.. _OpenStack cloud: https://github.com/NBISweden/LocalEGA/tree/dev/deployments/terraform
.. _available: https://github.com/NBISweden/LocalEGA/tree/dev/lega/conf/loggers
