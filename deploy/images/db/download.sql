CREATE SCHEMA local_ega_download;

SET search_path TO local_ega_download;

CREATE TABLE local_ega_download.requests (
   id                 SERIAL, PRIMARY KEY(id), UNIQUE (id),

   -- which files was downloaded
   file_id            INTEGER NOT NULL REFERENCES local_ega.main(id), -- No "ON DELETE CASCADE"
   start_coordinate   BIGINT DEFAULT 0,
   end_coordinate     BIGINT NULL, -- might be missing

   -- user info
   user_info         TEXT NULL,
   client_ip         TEXT NULL,
   
   created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- Insert new request, and return some vault information
CREATE TYPE request_type AS (req_id                    INTEGER,
                             header                    TEXT,
			     vault_path                TEXT,
			     vault_type                local_ega.storage,
			     file_size                 INTEGER,
			     unencrypted_checksum      VARCHAR,
			     unencrypted_checksum_type local_ega.checksum_algorithm);

CREATE FUNCTION make_request(sid    local_ega.main.stable_id%TYPE,
			     uinfo  local_ega_download.requests.user_info%TYPE,
			     cip    local_ega_download.requests.client_ip%TYPE,
                             scoord local_ega_download.requests.start_coordinate%TYPE DEFAULT 0,
                             ecoord local_ega_download.requests.end_coordinate%TYPE DEFAULT NULL)
RETURNS request_type AS $make_request$
#variable_conflict use_column
DECLARE
     req  local_ega_download.request_type;
     vault_rec local_ega.vault_files%ROWTYPE;
     rid  INTEGER;
BEGIN

     -- Find the file
     SELECT * INTO vault_rec FROM local_ega.vault_files WHERE stable_id = sid LIMIT 1;

     IF vault_rec IS NULL THEN
     	RAISE EXCEPTION 'Vault file not found for stable_id: % ', sid;
     END IF;

     -- New entry, or reuse old entry
     INSERT INTO local_ega_download.requests (file_id, user_info, client_ip, start_coordinate, end_coordinate)
     VALUES (vault_rec.file_id, uinfo, cip, scoord, ecoord)
     ON CONFLICT (id) DO NOTHING
     RETURNING local_ega_download.requests.id INTO rid;
     
     -- result
     req.req_id                    := rid;
     req.header                    := vault_rec.header;
     req.vault_path                := vault_rec.vault_path;
     req.vault_type                := vault_rec.vault_type;
     req.file_size                 := vault_rec.vault_filesize;
     req.unencrypted_checksum      := vault_rec.unencrypted_checksum;
     req.unencrypted_checksum_type := vault_rec.unencrypted_checksum_type;
     RETURN req;
END;
$make_request$ LANGUAGE plpgsql;


CREATE TABLE local_ega_download.success (
   id          SERIAL, PRIMARY KEY(id), UNIQUE (id),

   -- which requested file it was
   req_id      INTEGER NOT NULL REFERENCES local_ega_download.requests(id), -- No "ON DELETE CASCADE"

   -- Stats
   bytes       BIGINT DEFAULT 0,
   speed       FLOAT  DEFAULT 0.0, -- bytes per seconds

   -- table logs
   occured_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);


-- Mark a download as complete, and calculate the speed
CREATE FUNCTION download_complete(rid    local_ega_download.requests.id%TYPE,
       				  dlsize local_ega_download.success.bytes%TYPE,
          			  s      local_ega_download.success.speed%TYPE)
RETURNS void AS $insert_success$
BEGIN
     INSERT INTO local_ega_download.success(req_id,bytes,speed)
     VALUES(rid,dlsize,s);
END;
$insert_success$ LANGUAGE plpgsql;


-- ##################################################
--                      ERRORS
-- ##################################################
CREATE TABLE local_ega_download.errors (
   id          SERIAL, PRIMARY KEY(id), UNIQUE (id),
   req_id      INTEGER NOT NULL REFERENCES local_ega_download.requests(id), -- ON DELETE CASCADE,

   code        TEXT NOT NULL,
   description TEXT NOT NULL,

   -- where it happened
   hostname    TEXT,

   -- table logs
   occured_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_error(rid    local_ega_download.requests.id%TYPE,
			     h      local_ega_download.errors.hostname%TYPE,
                             etype  local_ega_download.errors.code%TYPE,
                             msg    local_ega_download.errors.description%TYPE)
RETURNS void AS $insert_error$
BEGIN
     INSERT INTO local_ega_download.errors (req_id,hostname,code,description)
     VALUES (rid, h, etype, msg);
END;
$insert_error$ LANGUAGE plpgsql;


-- ##################################################
--                      EBI views
-- ##################################################

CREATE VIEW local_ega_download.events AS
SELECT r.file_id          AS file_id
     , r.start_coordinate AS start_coordinate
     , r.end_coordinate   AS end_coordinate
     , r.user_info        AS email
     , r.client_ip        AS client_ip
     , e.code             AS event_type
     , e.description      AS event
FROM local_ega_download.errors e
INNER JOIN local_ega_download.requests r
ON r.id = e.req_id;
