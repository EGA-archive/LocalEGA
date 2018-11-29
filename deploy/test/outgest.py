#!/usr/bin/env python
import sys

import requests
# import json

TOKEN_URL = "https://egatest.crg.eu/idp/token"

# CLIENT_ID = "c1cdc493-8092-4f06-8a2d-5e042e71d39c"
# CLIENT_SECRET = 'AOJhe_3wrKHd12Z2K1fwchWOwmzQ3VFXNvGRc8S7jxnNBrtSy_SJB9rU_9STZHc7kmvE4SHN4sND5lY6-jiEj5I'
CLIENT_ID = "client"
CLIENT_SECRET = 'secret'

USERNAME = 'test@crg.eu'
PASSWORD = 'zhHSpkdK8KAn'

# Single call with resource owner credentials in the body
# and client credentials as the basic auth header
# => return access_token

headers = {'Accept': 'application/json',
           'Cache-Control': 'no-cache',
           'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

data = {"grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD}

r = requests.post(TOKEN_URL,
                  headers=headers,
                  data=data,
                  # verify=False,
                  allow_redirects=False,
                  auth=(CLIENT_ID, CLIENT_SECRET))

if r.status_code > 200:
    print('='*30, 'Headers', '='*3)
    print(r.headers)
    print('='*30, 'Body', '='*30)
    print(r.text)
    sys.exit(2)

reply = r.json()
oauth_token = reply['access_token']
print('Token:', oauth_token[:30], '...')

#####################################################################

STABLE_ID = 'EGAF00001398602'
OUTGEST_URL = 'http://localhost:10443'

pubkey = None
with open(sys.argv[2], 'rt') as f:
    pubkey = f.read()
    print('Pubkey:', pubkey)

print('Outgesting', STABLE_ID)

with requests.post(OUTGEST_URL,
                   headers={
                       'Authorization': 'bearer ' + oauth_token,
                   },
                   data={
                       'stable_id': STABLE_ID,
                       'pubkey': pubkey,
                   },
                   stream=True) as r:

    if r.status_code > 200:
        print('='*30, 'Headers', '='*30)
        print(r.headers)
        print('='*30, 'Body', '='*30)
        print(r.text)
        sys.exit(2)

    print('Outputing response into output.c4gh')
    with open(sys.argv[1], 'wb') as f:
        f.write(r.content)
