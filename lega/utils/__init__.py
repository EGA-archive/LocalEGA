import logging

LOG = logging.getLogger('utils')

def get_file_content(f):
    try:
        with open( f, 'rb') as h:
            return h.read()
    except OSError as e:
        LOG.error(f'Error reading {f}: {e!r}')
        return None

def sanitize_user_id(user):
    '''Removes the elixir_id from data and adds user_id instead'''

    # Elixir id is of the following form:
    # [a-z_][a-z0-9_-]*? that ends with a fixed @elixir-europe.org

    return user.split('@')[0]
    
