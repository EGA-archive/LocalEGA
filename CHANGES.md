# Version 1.2

* Less MQ connection sockets: one federated queue, one shovel (and added message ``type`` to distinguish the messages)
* MQ Heartbeat are reintroduced
* ingest and verify are one service: Since we were loading the data in memory, we also decrypt, checksum and move it to a staging area
* 2 instances of a backup microservice are added. Obviously, this is for illustration purpose only, each LocalEGA site might already have their own backup system. Nevertheless, a trust/confirmation is sent to CentralEGA.
* Database pipeline segregated from the main final database
* A save2db service is introduced at the end of the pipeline to save information in the long-term storage database (not the pipeline DB). It can handle also handle the dataset mappings (as a job of type `mapping`).
* Correlation IDs are used for each inbox upload/rename/deletion. However, when several message types are emitted by CentralEGA, the same correlation ID might be reused. Therefore, we introduce a `job_id`, handled by the database. The latter generates new job id if necessary (detecting if repeated messages).
* No leaked information from the LocalEGAs to CentralEGA. We only use checksums and public information
* Support for S3 has been factorized out from the code. The code is smaller and simpler. In order to support an S3-backed storage, the system administrator can for example use [S3-fuse filesystem](https://github.com/s3fs-fuse/s3fs-fuse)
* The pipeline database and mq docker images are migrated back into this repo

# Version 1.1
