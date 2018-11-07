-- SET search_path TO local_ega_download;

-- Used by EBI
CREATE VIEW local_ega_download.ebi_files AS
SELECT stable_id                 AS file_id,
       CASE
       WHEN (vault_file_type = 'S3') THEN 's3://'
       ELSE 'file://' -- enum: if not s3, then it's POSIX
       END || vault_file_reference AS file_name,
       vault_file_size           AS file_size,
       header                    AS header,
       vault_file_checksum       AS unencrypted_checksum,
       vault_file_checksum_type  AS unencrypted_checksum_type
FROM local_ega.main
WHERE status = 'READY';
