.. _`inbox login system`:

Inbox login system
==================

Central EGA contains a database of users, with IDs and passwords.

We have developped an NSS+PAM solution to allow user
authentication via either a password or an RSA key against the
CentralEGA database itself. The user is chrooted into their home
folder.

The solution uses CentralEGA's user IDs but can also be extended to
use Elixir IDs (of which we handle the @elixir-europe.org suffix by
stripping it).


The procedure is as follows. The inbox is started without any created
user. When a user wants log into the inbox (actually, only sftp
uploads are allowed), the NSS module looks up the username in a local
database, and, if not found, queries the CentralEGA database. Upon
return, we stores the user credentials in the local database and
create the user's home folder. The user now gets logged in if the
password or public key authentication succeeds. Upon subsequent login
attempts, only the local database is queried, until the user's
credentials expire, making the local database effectively acts as a
cache.

The user's homefolder is created when its credentials are retrieved
from CentralEGA. Moreover, for each user, we use FUSE mountpoint and
chroot the user into it. The FUSE application is in charge of
detecting when the file upload is completed and computing its
checksum. This information is provided to CentralEGA via a
:doc:`shovel mechanism on the local message broker <connection>`.

----

After proper configuration, there is no user maintenance, it is
automagic. The other advantage is to have a central location of the
EGA users.

Note that it is also possible to add non-EGA users if necessary, by
adding them to the local database, and specifing a
non-expiration/non-flush policy for those users.


Implementation
--------------

We use OpenSSH (version 7.5p1) and its ``sftp`` component. The NSS+PAM
source code has its own `repository
<https://github.com/NBISweden/LocalEGA-auth>`_. A makefile is provided
to compile and install the necessary shared libraries.

We copied the ``/sbin/sshd`` into an ``/sbin/ega`` binary and configured
the *ega* service by adding a file into the ``/etc/pam.d`` directory. In
this case, name the file ``/etc/pam.d/ega``.

.. literalinclude:: /../deployments/docker/images/inbox/pam.ega

The *ega* service is configured as ``sshd`` would. We only use the
``-c`` switch to specify where the configuration file is. The service
runs for the moment on port 9000.

Note that when PAM is configured as above, and a user is either not
found, or its authentication fails, the access to the service is
denied. No other user (not even root), other than Central EGA users,
have access to that service.

The authentication code of the library (ie the ``auth`` *type*) checks
whether the user has a valid ssh public key. If it is not the case,
the user is prompted to input a password. Central EGA stores password
hashes using the `BLOWFISH
<https://en.wikipedia.org/wiki/Blowfish_(cipher)>`_ hashing
algorithm. LocalEGA supports also the usual ``MD5``, ``SHA256`` and
``SHA512`` available on most Linux distribution (They are part of the
C library).

The ``account`` *type* of the PAM module checks if the account has
expired. If not, it "refreshes" it.

The ``session`` *type* handles the FUSE mount and chrooting.

Updating a user password is not allowed (ie therefore the ``password``
*type* is configure to deny every access).
