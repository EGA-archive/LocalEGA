# LocalEGA database definitions and docker image

We use
[Postgres 12.1](https://github.com/docker-library/postgres/tree/0d0485cb02e526f5a240b7740b46c35404aaf13f/12/alpine)
and Alpine 3.10.

Security is hardened:
- We do not use 'trust' even for local connections
- Requiring password authentication for all
- Using scram-sha-256 is stronger than md5
- Enforcing TLS communication
- Enforcing client-certificate verification

## Configuration

There are 2 users (`lega_in` and `lega_out`), and 2 schemas
(`local_ega` and `local_ega_download`).

The following environment variables can be used to configure the database:

| Variable                | Description                      | Default value |
|------------------------:|:---------------------------------|:--------------|
| PGDATA                  | The data directory               | `/ega/data`   |
| DB\_LEGA\_IN\_PASSWORD  | `lega_in`'s password             | -             |
| TZ                      | Timezone for the Postgres server | Europe/Madrid |


<a title="See Initialization scripts" href="https://hub.docker.com/_/postgres">As usual</a>, include your own `.sh`, `.sql` or `.sql.gz` files in `/docker-entrypoint-initdb.d/` in order to have them included at initialization time.

## TLS support

| Variable         | Description                                      | Default value      |
|-----------------:|:-------------------------------------------------|:-------------------|
| PG\_SERVER\_CERT | Public Certificate in PEM format                 | `/etc/ega/pg.cert` |
| PG\_SERVER\_KEY  | Private Key in PEM format                        | `/etc/ega/pg.key`  |
| PG\_CA           | Public CA Certificate in PEM format              | `/etc/ega/CA.cert` |
| PG\_VERIFY\_PEER | Enforce client verification                      | 0                  |
| SSL\_SUBJ        | Subject for the self-signed certificate creation | `/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=SysDevs/CN=LocalEGA/emailAddress=all.ega@crg.eu` |

If not already injected, the files located at `PG_SERVER_CERT` and `PG_SERVER_KEY` will be generated, as a self-signed public/private certificate pair, using `SSL_SUBJ`.

Client verification is enforced if and only if `PG_CA` exists and `PG_VERIFY_PEER` is set to `1`.

