CREATE SCHEMA local_ega_ebi;

SET search_path TO local_ega_ebi;

-- Special view for EBI Data-Out
CREATE VIEW local_ega_ebi.file AS
SELECT stable_id                                AS file_id,
       archive_file_reference                   AS file_name,
       archive_file_reference                   AS file_path,
       reverse(split_part(reverse(submission_file_path::text), '/'::text, 1)) AS display_file_name,
       archive_file_size                        AS file_size,
       NULL::text                               AS checksum,
       NULL::text                               AS checksum_type,
       archive_file_checksum                    AS unencrypted_checksum,
       archive_file_checksum_type               AS unencrypted_checksum_type,
       status                                   AS file_status,
       header                                   AS header
FROM local_ega.main
WHERE status = 'READY';

-- Relation File EGAF <-> Dataset EGAD
CREATE TABLE local_ega_ebi.filedataset (
       id       SERIAL, PRIMARY KEY(id), UNIQUE (id),
       file_id     INTEGER NOT NULL REFERENCES local_ega.main (id) ON DELETE CASCADE, -- not stable_id
       dataset_stable_id  TEXT NOT NULL
);

-- This view was created to be in sync with the entity eu.elixir.ega.ebi.downloader.domain.entity.FileDataset
-- which uses a view and has an @Id annotation in file_id
CREATE VIEW local_ega_ebi.file_dataset AS
SELECT m.stable_id AS file_id, dataset_stable_id as dataset_id FROM local_ega_ebi.filedataset fd
INNER JOIN local_ega.main m ON fd.file_id=m.id;

-- Relation File <-> Index File
CREATE TABLE local_ega_ebi.fileindexfile (
       id       SERIAL, PRIMARY KEY(id), UNIQUE (id),
       file_id     INTEGER NOT NULL REFERENCES local_ega.main (id) ON DELETE CASCADE, -- not stable_id
       index_file_id TEXT,
       index_file_reference      TEXT NOT NULL,     -- file path if POSIX, object id if S3
       index_file_type           local_ega.storage  -- S3 or POSIX file system
);

-- This view was created to be in sync with the entity eu.elixir.ega.ebi.downloader.domain.entity.FileIndexFile
-- which seems to use a view and has an @Id annotation in file_id
CREATE VIEW local_ega_ebi.file_index_file AS
SELECT m.stable_id AS file_id, index_file_id FROM local_ega_ebi.fileindexfile fif
INNER JOIN local_ega.main m ON fif.file_id=m.id;
