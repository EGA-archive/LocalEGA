Installation
============

.. highlight:: shell

Local EGA is an event-driven microservice architecture, with
(scalable) containers connected to a local message broker, and storing
long-lived information into a database.

The local message broker is itself connected to the CentralEGA message broker.

The sources for LocalEGA can be downloaded and installed from the `EGA-archive Github repo`_.

.. code-block:: console

    $ pip install git+https://github.com/EGA-archive/LocalEGA.git

However, we containerized the code and use `Docker`_ to deploy it.
Since there are several components with multiple settings, we created
a bootstrap script to help deploy a LocalEGA instance, on your local
machine. The sources for the external components are in seperate
repositories, i.e., the `inbox`_, the `local message broker`_ and the
`database`_, and will be pulled in when booting the instance.

The bootstrap generates random passwords, configuration files,
necessary public/secret keys, certificates for secure communication
and connect the different components together (via docker-compose
files). Moreover, the bootstrap creates a few test users and a fake
CentralEGA instance, to demonstrate the connection.

In the ``deploy`` directory, run the following command. All
interesting settings are found in the ``private`` sub-directory.

.. code-block:: console

    $ make -C bootstrap


Once the bootstrap files are generated, you can spin up the LocalEGA components, using:

.. code-block:: console

    $ make up

The docker images are automatically generated on `docker hub`_, and will be pulled with booting.

Use ``make ps`` to see its status.

.. note:: **Production deployments**: `Our partners`_ developed
	  alternative bootstrap methods for `Docker Swarm`_ and
	  `Kubernetes`_. Those methods allow you to deploy a LocalEGA
	  instance in a production environment, including scaling and
	  monitoring/healthcheck.


.. _EGA-archive Github repo: https://github.com/EGA-archive/LocalEGA
.. _Docker: https://github.com/EGA-archive/LocalEGA/tree/master/deploy
.. _Docker Swarm: https://github.com/neicnordic/LocalEGA-deploy-swarm
.. _Kubernetes: https://github.com/neicnordic/LocalEGA-deploy-init
.. _Openstack: https://github.com/NBISweden/LocalEGA-deploy-terraform
.. _Our partners: https://github.com/neicnordic/LocalEGA
.. _inbox: https://github.com/EGA-archive/LocalEGA-inbox
.. _local message broker: https://github.com/EGA-archive/LocalEGA-mq
.. _database: https://github.com/EGA-archive/LocalEGA-db
.. _docker hub: https://hub.docker.com/orgs/egarchive/repositories
