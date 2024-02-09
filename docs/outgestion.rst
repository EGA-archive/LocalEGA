.. _`distribution`:

Data Distribution
=================

Architecture
------------

The distribution service is a server mounting a FUSE filesystem per user automatically to stitch Crypt4GH headers to file payloads and serve them over SFTP. The headers are specially re-encrypted for each user on-the-fly, and dataset permissions are checked live.

It comprises the following components:

.. image:: /static/distribution.jpg
   :target: ./_static/distribution.jpg
   :alt: Distribution Architecture and Connected Components

The reference implementation uses a microservice architecture with an internal database, a long-term storage compatible with FUSE, and a SFTP server connected to this FUSE FS.

.. raw:: html
   :file: outgestion.html


Installation
------------

A reference implementation can be found in the `Local EGA Distribution Github repository`_. 

Since there are several components, we provide several README for the deployment of each: NSS, PAM and SFTP server, as well as, new functions that must be added to the main database.

To test that the deployment works, receiving a permission for user ``jane`` can be triggered by ``make permission``. Bear in mind that this requires to have run the ingestion test, so there is at least one file successfully archived and the dataset ``EGAD90000000123`` is released.
Then you can run:

.. code-block:: console

   sftp jane@localhost                                                         # Connect user Jane with password: jane
   get example.txt.c4gh                                                        # download the file
   crypt4gh decrypt --sk cega/users/jane.key < example.txt.c4gh > example.txt  # decrypt the file downloaded with jane's key
   diff example.txt data/example.txt                                           # compare content of the decrypted file and the original one


.. _Local EGA Distribution Github repository: https://github.com/EGA-archive/LocalEGA-distribution