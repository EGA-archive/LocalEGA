
-- ################################################
-- Rebuild the users cache
-- ################################################
CREATE OR REPLACE FUNCTION fs.make_nss_users()
RETURNS void
LANGUAGE plpgsql
AS $BODY$
BEGIN
	RAISE NOTICE 'Updating users in /ega/cache/nss/users';
	COPY (SELECT username,
	     	     'x', -- no password
	             uid,
		     gid,
		     gecos,
		     homedir,
		     shell
	       FROM public.requesters
        )
	TO '/ega/cache/nss/users'
	WITH DELIMITER ':'
	     NULL '';
END;
$BODY$;

CREATE OR REPLACE FUNCTION fs.trigger_nss_users()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $BODY$
BEGIN
	PERFORM * FROM fs.make_nss_users();
	RETURN NULL; -- result is ignored since this is an AFTER trigger
END;
$BODY$;

CREATE OR REPLACE TRIGGER build_nss_users
AFTER INSERT OR UPDATE OR DELETE
ON public.user_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_users();


-- ################################################
-- Rebuild the passwords cache (ie shadow)
-- ################################################
CREATE OR REPLACE FUNCTION fs.make_nss_passwords()
RETURNS void
LANGUAGE plpgsql VOLATILE
AS $BODY$
BEGIN
	RAISE NOTICE 'Updating passwords';
	COPY (SELECT DISTINCT
	             u.username,
  		     COALESCE(upt.password_hash, '*'),
		     '18949','0','99999','7', '', '', ''
	      FROM public.requesters u
	      LEFT JOIN private.user_password_table upt ON upt.user_id = u.db_uid AND upt.is_enabled
	)
	TO '/ega/cache/nss/passwords'
	WITH DELIMITER ':'
	     NULL '';
END;
$BODY$;

CREATE OR REPLACE FUNCTION fs.trigger_nss_passwords()
RETURNS TRIGGER
LANGUAGE plpgsql VOLATILE
AS $BODY$
BEGIN
	PERFORM * FROM fs.make_nss_passwords();
	RETURN NULL; -- result is ignored since this is an AFTER trigger
END;
$BODY$;

CREATE OR REPLACE TRIGGER build_nss_passwords
AFTER INSERT OR UPDATE OR DELETE
ON private.user_password_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_passwords();


-- ################################################
-- Rebuild the groups cache
-- ################################################
CREATE OR REPLACE FUNCTION fs.make_nss_groups()
RETURNS void
LANGUAGE plpgsql
AS $BODY$
BEGIN
        RAISE NOTICE 'Updating groups';
        -- We only create one group with all the requesters: gid=10000
        COPY (
           SELECT 'requesters' AS name,
                  'x'          AS password, -- no password 
                  20000          AS gid,
                  string_agg(DISTINCT r.username::text, ',') AS members
           FROM public.requesters r
        )
        TO '/ega/cache/nss/groups'
        DELIMITER ':' NULL '';
END;
$BODY$;

CREATE OR REPLACE FUNCTION fs.trigger_nss_groups()
RETURNS TRIGGER
LANGUAGE plpgsql VOLATILE
AS $BODY$
BEGIN
	PERFORM * FROM fs.make_nss_groups();
	RETURN NULL; -- result is ignored since this is an AFTER trigger
END;
$BODY$;

CREATE OR REPLACE TRIGGER build_nss_groups
AFTER INSERT OR UPDATE OR DELETE
ON public.group_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_groups();


CREATE OR REPLACE TRIGGER build_nss_users_groups
AFTER INSERT OR UPDATE OR DELETE
ON public.user_group_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_groups();



-- ################################################
-- Rebuild the keys cache
-- ################################################

CREATE OR REPLACE FUNCTION fs.make_authorized_keys(_user_id bigint)
RETURNS void
LANGUAGE plpgsql
AS $BODY$
DECLARE
	_username text := NULL;
	_query text;
BEGIN
	SELECT username INTO _username
	FROM public.user_table
	WHERE id=_user_id;

	IF _username IS NULL THEN
	   RAISE EXCEPTION 'User % not found', _user_id;
	END IF;

	_query := format('COPY (SELECT key FROM public.ssh_keys WHERE uid = %s)
	                  TO ''/ega/cache/authorized_keys/%s'';', _user_id, public.db2sys_user_id(_user_id)::text);
	RAISE NOTICE 'Updating keys for /ega/cache/authorized_keys/% (%)', public.db2sys_user_id(_user_id), _username;
	EXECUTE _query;
END;
$BODY$;

CREATE OR REPLACE FUNCTION fs.trigger_authorized_keys()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $BODY$
DECLARE
	_user_id bigint;
BEGIN

	IF TG_OP='DELETE' THEN
		_user_id= OLD.user_id;
	ELSE -- if insert or update
		_user_id = NEW.user_id;
	END IF;

	PERFORM * FROM fs.make_authorized_keys(_user_id);

	IF TG_OP='DELETE' THEN
		RETURN OLD; -- https://www.postgresql.org/docs/14/plpgsql-trigger.html
		            -- See: 'The usual idiom in DELETE triggers is to return OLD'
	ELSE
		RETURN NEW;
	END IF;
END;
$BODY$;

CREATE OR REPLACE TRIGGER build_authorized_keys
AFTER INSERT OR UPDATE OR DELETE
ON public.user_key_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_authorized_keys();

CREATE OR REPLACE TRIGGER build_users_from_authorized_keys
AFTER INSERT OR UPDATE OR DELETE
ON public.user_key_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_users();

CREATE OR REPLACE TRIGGER build_groups_from_authorized_keys
AFTER INSERT OR UPDATE OR DELETE
ON public.user_key_table
FOR EACH ROW
EXECUTE PROCEDURE fs.trigger_nss_groups();

