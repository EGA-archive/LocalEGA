Testsuite
=========

We have implemented several types of `testsuite`_, grouped into one of
the following categories: *unit tests*, *integration tests*,
*robustness tests*, *security tests*, and *stress tests*.

All but the unit tests simulate real-case user scenarios on how they
will interact with the system. All tests are performed on GitHub
Actions runner, when there is a push to master or a Pull Request
creation (i.e., they are integrated to the CI).

|moreabout| Check out the `list of tests`_.

Unit Tests
^^^^^^^^^^

Unit tests test the functionalities of the code, and are by design
minimal: Given a set of input values for a chosen function, they
execute the function and check if the output has the expected
values. Moreover, they capture triggered exceptions and
errors. Additionally we also perform pep8 and pep257 style guide
checks using `flake8 <http://flake8.pycqa.org/en/latest/>`_ (ignoring
the trivial configurations such as E226, D203, D212, D213, D404, D100,
D104, C901, E402, W503, W504):

Unit tests can be run using the ``tox`` command.

.. code-block:: console

    $ tox

Integration Tests
^^^^^^^^^^^^^^^^^

Integration tests are more involved and simulate how a user will use
the system. They test the overall ingestion architecture.

.. code-block:: console

    $ bats tests/integration

Robustness Tests
^^^^^^^^^^^^^^^^

Robustness tests test the microservice architecture and how the
components are inter-connected. They, for example, check that if the
database or one microservice is restarted, the overall functionality
remains.

.. code-block:: console

    $ bats tests/robustness

Security Tests
^^^^^^^^^^^^^^

Security tests increase confidence around security of the
implementation. They give some deployment guarantees, such as one user
cannot see the inbox of another user, or the vault is not accessible
from the inbox.

.. code-block:: console

    $ bats tests/security

Stress Tests
^^^^^^^^^^^^

Not yet implemented

.. _testsuite: https://github.com/EGA-archive/LocalEGA/tree/master/tests
.. |moreabout| unicode:: U+261E .. right pointing finger
.. _list of tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests
