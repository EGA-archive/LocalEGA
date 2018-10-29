.. _`testsuite`:

Testsuite
=========

We have implemented 2 types of testsuite: one set of *unit tests* to
test the functionalities of the code and one set of *integration
tests* to test the overall architecture. The latter does actually
deploy the docker setup and runs several scenarios, simulating how users
will utilize the system as a whole.

Unit Tests
^^^^^^^^^^

Unit tests are minimal: Given a set of input values for a chosen
function, they execute the function and check if the output has the
expected values. Moreover, they capture triggered exceptions and
errors. Unit tests can be run using the ``tox`` commands.

.. code-block:: console

    $ cd [git-repo]
    $ tox

Integration Tests
^^^^^^^^^^^^^^^^^

.. note:: todo
