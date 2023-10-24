# Local EGA main repository


[![Documentation Status](https://readthedocs.org/projects/localega/badge/?version=latest)](https://localega.readthedocs.io/en/latest/?badge=latest)
[![Testsuite](https://github.com/EGA-archive/LocalEGA/workflows/Testsuite/badge.svg)](https://github.com/EGA-archive/LocalEGA/actions)


The [code](ingestion/lega) is written in Python (3.7+).

You can provision and deploy the different components, locally, using [docker-compose](deploy).

## Quick install

	cd deploy/docker
	# Rename the *.sample files, and update their sensitive information
	docker-compose up -d 

After a few seconds, you then have a locally-deployed instance of
LocalEGA (using a fake Central EGA), and you can run the
[testsuite](tests).

## Architecture

Find the [LocalEGA documentation](http://localega.readthedocs.io) hosted on [ReadTheDocs.org](https://readthedocs.org/).

![Architecture](docs/static/overview.png)

