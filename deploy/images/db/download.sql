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

-- Insert new request, and return some archive information
CREATE TYPE request_type AS (req_id                    INTEGER,
                             header                    TEXT,
			     archive_path                TEXT,
			     archive_type                local_ega.storage,
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
     archive_rec local_ega.archive_files%ROWTYPE;
     rid  INTEGER;
BEGIN

     -- Find the file
     SELECT * INTO archive_rec FROM local_ega.archive_files WHERE stable_id = sid LIMIT 1;

     IF archive_rec IS NULL THEN
     	RAISE EXCEPTION 'archived file not found for stable_id: % ', sid;
     END IF;

     -- New entry, or reuse old entry
     INSERT INTO local_ega_download.requests (file_id, user_info, client_ip, start_coordinate, end_coordinate)
     VALUES (archive_rec.file_id, uinfo, cip, scoord, ecoord)
     ON CONFLICT (id) DO NOTHING
     RETURNING local_ega_download.requests.id INTO rid;
     
     -- result
     req.req_id                    := rid;
     req.header                    := archive_rec.header;
     req.archive_path              := archive_rec.archive_path;
     req.archive_type              := archive_rec.archive_type;
     req.file_size                 := archive_rec.archive_filesize;
     req.unencrypted_checksum      := archive_rec.unencrypted_checksum;
     req.unencrypted_checksum_type := archive_rec.unencrypted_checksum_type;
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

