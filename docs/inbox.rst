.. _`inbox login system`:

Inbox login system
==================

Central EGA contains a database of users, with IDs and passwords
(which can already be extended to use Elixir IDs, of which we strip
the ``@elixir-europe.org`` suffix).

We have `developed a solution
<https://localega-inbox.readthedocs.io>`_ allowing user authentication
via either a password or an SSH key against CentralEGA database
itself. The procedure is as follows: the inbox is started without any
created user. When a user wants to log into the inbox (actually, only
``sftp`` uploads are allowed), the system looks up the username in a
local cache, and, if not found, queries the CentralEGA REST
endpoint. Upon return, we store the user credentials in the local
cache and create the user's home directory. The user now gets logged
in if the password or public key authentication succeeds. Upon
subsequent login attempts, only the local cache is queried, until the
user's credentials expire. The cache has a default TTL of one hour,
and is wiped clean upon reboot (as a cache should).

We installed a hook to detect when a file is (re)uploaded or
renamed. The hook runs a checksum on the uploaded file and notifies
CentralEGA via a :doc:`shovel mechanism on the local message broker
<connection>`.


.. note:: After proper configuration, there is no user maintenance, it is
   automagic. The other advantage is to have a central location of the
   EGA users.

   Moreover, it is also possible to add non-EGA users if necessary, by
   reproducing the same mechanism but outside the temporary
   cache. Those users will persist upon reboot.


See `its full documentation <https://localega-inbox.readthedocs.io>`_
or the `source code on its dedicated repository
<https://github.com/EGA-archive/LocalEGA-inbox>`_.
