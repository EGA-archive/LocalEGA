-- \connect lega

CREATE SCHEMA local_ega_audit;     -- includes logs, events

CREATE TYPE status AS ENUM ('INIT', 'FAILURE', 'SUCCESS'); -- add more status if necessary
       	    	      	   	    	       		   -- like, more stages

CREATE TABLE local_ega_audit.download (
   id                 SERIAL, PRIMARY KEY(id), UNIQUE (id),

   -- which files was downloaded
   file_id            INTEGER NOT NULL REFERENCES local_ega.main(id), -- No "ON DELETE CASCADE"

   -- Status/Progress
   status             status NOT NULL, -- DEFAULT 'INIT'
   
   -- by which tool
   api                VARCHAR(45) NOT NULL,

   -- Information about the client
   client_ip          VARCHAR(45) NOT NULL,
   email              VARCHAR(256) NOT NULL,
   token_source       VARCHAR(256) NOT NULL,

   -- Stats
   download_speed     FLOAT8 NULL, -- todo: indicate the unit
   start_coordinate   INT8 NOT NULL DEFAULT 0,
   end_coordinate     INT8 NOT NULL DEFAULT 0,
   bytes              INT8 NOT NULL DEFAULT 0,

   -- table logs
   created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
)
WITH (OIDS=FALSE);


CREATE TABLE local_ega_audit.event (
   id           SERIAL, PRIMARY KEY(id), UNIQUE (id),

   -- Wot iz dis?
   event        VARCHAR(256) NOT NULL,
   event_type   VARCHAR(256) NOT NULL,

   -- User info. ... eh... again?
   client_ip    VARCHAR(45) NOT NULL,
   email        VARCHAR(256) NOT NULL,

   -- table logs
   created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
)
WITH (OIDS=FALSE);


