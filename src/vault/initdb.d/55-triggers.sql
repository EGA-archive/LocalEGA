CREATE FUNCTION public.update_edited_columns()
RETURNS trigger
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
   NEW.edited_at = now();
   NEW.edited_by_db_user = current_user;

   RETURN NEW;
END;
$BODY$;

CREATE TRIGGER dataset_table_update_edited_columns
BEFORE UPDATE ON public.dataset_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();


CREATE TRIGGER dac_table_update_edited_columns
BEFORE UPDATE ON public.dac_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER dac_dataset_table_update_edited_columns
BEFORE UPDATE ON public.dac_dataset_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER dac_user_table_update_edited_columns
BEFORE UPDATE ON public.dac_user_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER dataset_file_table_update_edited_columns
BEFORE UPDATE ON public.dataset_file_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

-- public.file_table
CREATE TRIGGER file_table_update_edited_columns
BEFORE UPDATE ON public.file_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

-- private.file_table
CREATE TRIGGER file_table_update_edited_columns
BEFORE UPDATE ON private.file_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER user_table_update_edited_columns
BEFORE UPDATE ON public.user_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER group_table_update_edited_columns
BEFORE UPDATE ON public.group_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER user_group_table_update_edited_columns
BEFORE UPDATE ON public.user_group_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER user_key_table_update_edited_columns
BEFORE UPDATE ON public.user_key_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER user_password_table_update_edited_columns
BEFORE UPDATE ON private.user_password_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER dataset_permission_table_update_edited_columns
BEFORE UPDATE ON private.dataset_permission_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

CREATE TRIGGER permission_action_table_update_edited_columns
BEFORE UPDATE ON request.permission_action_table
FOR EACH ROW EXECUTE PROCEDURE public.update_edited_columns();

