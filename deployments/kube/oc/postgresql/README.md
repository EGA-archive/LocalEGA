## Openshift PostgreSQL

There are several ways of customising the PostgreSQL Pod, here we illustrate only some of them.

### s2i build

Creating an extension of the current image using: https://github.com/sclorg/postgresql-container/tree/generated/9.6#extending-image
instructions.
In order to achieve this we will need to create a custom `postgresql-start/` script with the following contents:

```bash
#!/bin/bash

psql -U postgres -d $POSTGRESQL_DATABASE -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
psql -U $POSTGRESQL_USER -d $POSTGRESQL_DATABASE -c "\i /scripts/db.sql"
```

The `/scripts` folder contains the `db.sql` as an configMap e.g.:

```
...
- mountPath: /scripts
  name: initdb

...
- name: initdb
  configMap:
    name: initsql
    items:
      - key: db.sql
        path: db.sql
```

After this we can create our own docker image following the instructions presented above:
```
$ s2i build ~/image-configuration/ postgresql new-postgresql
```

### configMap

> user provided files are preferred over default files in `/usr/share/container-scripts/`- so it is possible to overwrite them.

Considering the option of overwrite we can create our own custom map the contents of the https://github.com/sclorg/postgresql-container/tree/generated/9.6/root/usr/share/container-scripts/postgresql
in a configMap, by overwritting the `set_passwords.sh` script to contain the commands we need.

An example of the `Deployment` an `DeploymentConfig` YAML files are present in this directory.
