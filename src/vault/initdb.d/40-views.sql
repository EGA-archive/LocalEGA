
CREATE VIEW public.groups AS
SELECT name  AS groupname,
       id    AS gid
FROM public.group_table
WHERE is_enabled = true;

--
-- We return SSH keys only if at least one crypt4gh key exists for the given user
--
CREATE VIEW public.ssh_keys AS
SELECT --DISTINCT 
	ut.id 	AS uid,
       ut.username  AS username,
       uk.key       AS key
FROM public.user_key_table uk
INNER JOIN public.user_table ut ON ut.id = uk.user_id
WHERE (-- uk.is_enabled = true
       -- AND
       uk.key IS NOT NULL
       AND
       uk.type IN ('ssh'::public.key_type, 'ssh-ed25519'::public.key_type)
      );


CREATE VIEW public.header_keys AS
SELECT --DISTINCT 
       ut.id        AS user_id,
       ut.username  AS username,
       uk.key       AS key
FROM public.user_key_table uk
INNER JOIN public.user_table ut ON ut.id = uk.user_id
WHERE (-- uk.is_enabled = true
       -- AND
       uk.key IS NOT NULL
       AND
       uk.type IN ('c4gh-v1'::public.key_type, 'ssh-ed25519'::public.key_type)
      );


