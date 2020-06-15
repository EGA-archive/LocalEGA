Encryption Algorithm - Crypt4GH
===============================

The encryption procedure uses the `Crypt4GH file format
<https://crypt4gh.readthedocs.io>`_, which works as follows.

In a nutshell, the original file is encrypted with a symmetric
algorithm (here Chacha20), authenticated (here with Poly1305). The
resulting encrypted data is called the data portion. The data portion
is segmented. The symmetric key used for the encryption is called the
session key. The session key is unique for each file.

The session key is itself encrypted with the public key of a LocalEGA
instance, and prepended to the encrypted original file. The prepended
part is called the Crypt4GH header.

.. image:: https://crypt4gh.readthedocs.io/en/latest/_images/encryption.png
   :target: https://crypt4gh.readthedocs.io/en/latest/_images/encryption.png
   :alt: Encryption

There are several advantages for using `the Crypt4GH format
<http://samtools.github.io/hts-specs/crypt4gh.pdf>`_. The main ones
are:

* No re-encryption upon ingestion (only decryption).
* Minimal re-encryption for data distribution.
* Shipping only selected segments for data distribution.


.. image:: /static/Crypt4GH.png
   :target: ./_static/Crypt4GH.png
   :alt: Advantages of using Crypt4GH
