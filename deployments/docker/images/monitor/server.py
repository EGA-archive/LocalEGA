import sys
from aiohttp import web
import logging
import sqlite3


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)

conn = sqlite3.connect('status.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE if not exists status
               (instance text, service text, status int, exitStatus int)''')

async def status_handler(request):
    data = await request.json()

    cursor.execute('SELECT * FROM status WHERE (instance=? AND service=?)', (data['instance'], data['service']))
    entry = cursor.fetchone()

    if entry is None:
        cursor.execute('INSERT INTO status (instance, service, status, exitStatus) VALUES (?,?,?,?)',
                       (data['instance'], data['service'], data['status'], data['exitStatus'] if 'exitStatus' in data else None, ))
        logger.info('New entry added.')
    else:
        cursor.execute('UPDATE status SET status = ?, exitStatus = ? WHERE instance = ? and service = ?',
                       (data['status'], data['exitStatus'] if 'exitStatus' in data else None, data['instance'], data['service'], ))
        logger.info('Entry updated.')

    logger.info(data)
    return web.Response(text=str(data))


async def service_handler(request):
    service = request.match_info.get('service', '')
    instance = request.match_info.get('instance', '')
    cursor.execute('SELECT * FROM status WHERE (instance=? AND service=?)', (instance, service, ))
    entry = cursor.fetchone()

    if entry is None:
        logger.info('Entry not found')
        return web.Response(status=404)
    else:
        logger.info(entry)
        if entry[3] is None:
            data = {'instance': entry[0], 'service': entry[1], 'status': entry[2]}
        else:
            data = {'instance': entry[0], 'service': entry[1], 'status': entry[2], 'exitStatus': entry[3]}
        return web.json_response(data)

def main():

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"

    # loop = asyncio.get_event_loop()
    server = web.Application()

    # Registering the routes
    server.router.add_post('/status', status_handler)
    server.router.add_get('/{instance}/{service}', service_handler)

    web.run_app(server, host=host, port=5039, shutdown_timeout=0)


if __name__ == '__main__':
    main()
