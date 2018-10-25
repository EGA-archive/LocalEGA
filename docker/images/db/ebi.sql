
-- Special view for EBI Data-Out
CREATE VIEW local_ega.ebi_files AS
SELECT id                                       AS file_id,
       stable_id                                AS file_name,
       vault_file_reference                     AS file_path,
       vault_file_type                          AS file_type,
       vault_file_size                          AS file_size,
       vault_file_checksum                      AS unencrypted_checksum,
       vault_file_checksum_type                 AS unencrypted_checksum_type,
       header                                   AS header,
       created_by                               AS created_by,
       last_modified_by                         AS last_updated_by,
       created_at                               AS created,
       last_modified                            AS last_updated
FROM local_ega.main
WHERE status = 'READY';


-- Relation File <-> Index File
CREATE TABLE local_ega.index_files (
       id       SERIAL, PRIMARY KEY(id), UNIQUE (id),

       file_id  INTEGER NOT NULL REFERENCES local_ega.main (id) ON DELETE CASCADE,

       index_file_reference      TEXT NOT NULL,     -- file path if POSIX, object id if S3
       index_file_type           local_ega.storage  -- S3 or POSIX file system
);

-- Relation File EGAF <-> Dataset EGAD
CREATE TABLE local_ega.file2dataset (
       id       SERIAL, PRIMARY KEY(id), UNIQUE (id),

       file_id     INTEGER NOT NULL REFERENCES local_ega.main (id) ON DELETE CASCADE, -- not stable_id

       dataset_id  TEXT NOT NULL
);

-- Event
CREATE TABLE local_ega.event (
       event_id  SERIAL, UNIQUE (event_id),

       client_ip varchar(45) NOT NULL,

       event varchar(256) NOT NULL,

       event_type varchar(256) NOT NULL,

       email varchar(256) NOT NULL,

       created timestamp NOT NULL DEFAULT now(),

       CONSTRAINT event_pkey PRIMARY KEY (event_id)

);

-- Download Log
CREATE TABLE local_ega.download_log (
       download_log_id SERIAL, PRIMARY KEY(download_log_id), UNIQUE (download_log_id),

       client_ip varchar(45) NOT NULL,

       api varchar(45) NOT NULL,

       email varchar(256) NOT NULL,

       file_id varchar(15) NOT NULL,

       download_speed float8 NOT NULL DEFAULT '-1'::integer,

       download_status varchar(256) NOT NULL DEFAULT 'success'::character varying,

       encryption_type varchar(256) NOT NULL,

       start_coordinate int8 NOT NULL DEFAULT 0,

       end_coordinate int8 NOT NULL DEFAULT 0,

       bytes int8 NOT NULL DEFAULT 0,

       created timestamp NOT NULL DEFAULT now(),

       token_source varchar(255) NOT NULL

);
