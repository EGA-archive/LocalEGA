.. _bootstrap:

Bootstrap & Deployment
======================

In order to simplify the setup of LocalEGA's components, we have
developed a bootstrap script, taylored for the `Docker`_ deployment.

This script creates random passwords, configuration files, necessary
public/secret keys and connect the different components together.

All interesting settings are found in the ``private`` directory. Look
especially at the ``.trace`` file there.

.. note::
   You can find different deployment strategies, covered by our
   partners, for environments like `Docker Swarm`_, `Kubernetes`_, `Openstack`_.


.. _Docker: https://github.com/EGA-archive/LocalEGA/tree/master/deploy

.. _Docker Swarm: https://github.com/NBISweden/LocalEGA-deploy-swarm
.. _Kubernetes: https://github.com/NBISweden/LocalEGA-deploy-k8s
.. _Openstack: https://github.com/NBISweden/LocalEGA-deploy-terraform
