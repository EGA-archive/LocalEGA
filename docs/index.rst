================
Local EGA
================

.. raw:: html

   <div class="youtube_wrapper">
      <iframe allowfullscreen="true" src="https://www.youtube.com/embed/k9R8W3V3ugU">
      </iframe>
      <div class="caption">Symposium held on 2020, specific details might no longer apply</div>
   </div>

.. raw:: latex

   \begin{quote}\begin{center}\fbox{\url{https://youtu.be/k9R8W3V3ugU}}\end{center}\end{quote}

..
   .. image:: /static/CEGA-LEGAs.png
      :alt: Central EGA and Local EGAs, in a nutshell
      :class: img-right
      :target: https://www.youtube.com/watch?v=k9R8W3V3ugU

The ``Local EGA`` project consists of several components:

* An inbox
* A long-term database and file storage
* An ingestion pipeline
* A distribution system

It aims at solving the issue where sensitive data cannot move across
borders (cf to GDPR), while public metadata can. Files will be stored
encrypted in the Local EGAs located in different countries, while
public metadata stays at Central EGA.

In short, submitters
upload encrypted files into a Local EGA inbox, located in the relevant
country. The ingestion pipeline moves the encrypted files from the
inbox into the long-term storage, and saves information in the
database. In the process, each ingested file obtain an ``Accession
ID``, which identifies it uniquely across `the EGA <https://ega-archive.org/>`_. The distribution system allows
requesters to access securely the encrypted files in the long-term
storage, using the accession id, if permissions are granted by a Data
Access Commity (``DAC``).

.. image:: /static/CEGA-FEGA.png
   :target: ./_static/CEGA-FEGA.png
   :alt: General Architecture and Connected Components


Files are encrypted whether in transit or at rest. The transport
depends on the inbox and files are stored using the `Crypt4GH file format <http://samtools.github.io/hts-specs/crypt4gh.pdf>`_. The
metadata of the encrypted files and the permissions to access them are
located at ``Central EGA``.

----

More concretely, the workflow consists of three ordered parts,
involving 2 different user roles: submitters and requesters.

The submitter first logs onto the Local EGA's inbox and uploads its
encrypted files. Login credentials are provided by Central EGA. For
every uploaded file, Central EGA receives a notification that the file
has landed. The file is checksumed and presented in the Central EGA's
interface in order for the user to double-check the integrity of the
upload.

|moreabout| More details about the :ref:`inbox login system`.

The submitter then prepares a submission, programmatically or via
Central EGA's interface. Upon completion, Central EGA sends an
ingestion trigger to the connected Local EGA, and the files are moved
securely into the long-term storage. They also obtain their Accession
ID, identifying them uniquely across Central EGA and all Local EGAs
(or rather, their *content*).

|moreabout| More details about the :ref:`ingestion process`.

Separately, after a file is successfully ingested (including a backup
confirmation), has an accession id, and the metadata is marked as
*released*, the file becomes available for download. If a file access
has been granted by a DAC, the file can be served in Crypt4GH format
to the requester.

|moreabout| More details about the :ref:`distribution`.

Permissions are granted by the DACs (and not Central EGA). Central EGA
and Local EGAs are not the files' owner. Ownership is retained by the
DACs, as a result of consent agreements signed by the submitters whom
provided the original files.

|moreabout| More details about the `EGA access model <https://ega-archive.org/access/request-data/how-to-request-data/>`_.

----

.. toctree::
   :maxdepth: 1

   Connection CEGA-LEGA <amqp>
   Inbox                <inbox>
   Ingestion            <ingestion>
   Distribution         <outgestion>
   Encryption           <encryption>
   Contributing         <https://github.com/EGA-archive/LocalEGA/blob/master/CONTRIBUTING.md>



.. |moreabout| unicode:: U+261E .. right pointing finger
