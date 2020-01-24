Throughout this documentation, we can refer to Central EGA as
``CEGA``, or ``CentralEGA``, and *any* Local EGA instance as ``LEGA``,
or ``LocalEGA``.  When two or more Local EGA instances are involved,
we will use ``LEGA<i>`` for Local EGA instance ``<i>``.

================
Local EGA
================

The Local EGA project is divided into several microservices.

.. raw:: html
   :file: table.html

The workflow consists of two ordered parts:

The user first logs onto the Local EGA's inbox and uploads its
files. He/She then goes to the Central EGA's interface to prepare a
submission. Upon completion, the files are ingested into the archive and
become searchable by the Central EGA's engine.

----

More concretely, Central EGA contains a database of users. The Central
EGA' ID is used to authenticate the user against either their EGA
password or an RSA key.

For every uploaded file, Central EGA receives a notification that the
file has landed. The file is checksumed and presented in the Central
EGA's interface in order for the user to double-check that it was
properly uploaded.

|moreabout| More details about the :ref:`inbox login system`.

When a submission is ready, Central EGA triggers an ingestion process
on the user-chosen Local EGA instance. The uploaded file must be
encrypted in the `Crypt4GH file format
<https://crypt4gh.readthedocs.io/en/latest/encryption.html>`_ using
that Local EGA's public key. Central EGA's interface is updated with
progress notifications whether the ingestion was successful, or
whether there was an error.

|moreabout| More details about the :ref:`ingestion process`.

.. image:: /static/components.jpeg
   :target: ./_static/components.jpeg
   :alt: General Architecture and Connected Components

----

.. toctree::
   :maxdepth: 1
   :name: architecture

   Installation         <installation>
   Ingestion            <ingestion>
   Data distribution    <outgestion>
   Encryption           <encryption>
   Connection CEGA-LEGA <connection>
   Inbox                <inbox>
   Testsuite            <tests>
   Contributing         <contribute>

|Testsuite| | Version |version| | Generated |today|


.. |Testsuite| image:: https://github.com/EGA-archive/LocalEGA/workflows/Testsuite/badge.svg
	:alt: Testsuite Status
	:class: inline-baseline

.. |moreabout| unicode:: U+261E .. right pointing finger
