import logging

LOG = logging.getLogger('utils')

def sanitize_user_id(data):
    '''Removes the elixir_id from data and adds user_id instead'''

    # Elixir id is of the following form:
    # [a-z_][a-z0-9_-]*? that ends with a fixed @elixir-europe.org

    user_id = data['elixir_id'].split('@')[0]
    del data['elixir_id']
    data['user_id'] = user_id
    return user_id
