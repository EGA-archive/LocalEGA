.. _`testsuite`:

We have implemented 2 types of testsuite: one set of *unit tests* to
test the functionalities of the code and one set of *integration
tests* to test the overall architecture. The latter does actually
deploy a chosen setup and runs several scenarios, simulating how users
will utilize the system as a whole.

Unit Tests
==========

Unit tests are minimal: Given a set of input values for a chosen
function, they execute the function and check if the output has the
expected values. Unit tests can be run using the ``tox`` commands.

.. code-block:: console

    $ cd [git-repo]/tests
    $ tox

Integration Tests
=================

Integration tests are more involved and simulate how a user will use
the system. Therefore, we have develop a `bootstrap script <>` to
kickstart the system, and we execute a set of scenari in it. `The
implementation
<https://github.com/NBISweden/LocalEGA/blob/dev/deployments/docker/tests/README.md>`
is in Java.

.. code-block:: console

    $ cd [git-repo]/deployments/docker/tests
    $ mvn test -B

Here is a description of the different `scenari we currently test
<https://github.com/NBISweden/LocalEGA/wiki/Testing-LocalEGA>`.
