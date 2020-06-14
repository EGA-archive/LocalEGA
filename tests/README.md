# LocalEGA testsuite

Unit Tests are run with pytest, coverage and tox.

The other tests use [BATS](https://github.com/bats-core/bats-core).
They also require `expect`, `ssh`, `ssh-agent` and `crypt4gh`.

Install the required packages with `pip install -r requirements.txt`.

## Integration Tests

These tests treat the system as a black box, only checking the expected output for a given input.

      $ bats tests/integration

- [x] Ingesting a 10MB file<br/>
      Expected outcome: Message in the CentralEGA completed queue
  
- [x] Ingesting a ["big" file](integration/ingestion.bats#L73-L76)<br/>
      Expected outcome: Message in the CentralEGA completed queue

- [x] Ingesting a directory with multiple files and/or subdirectories<br/>
      Expected outcome: Messages in the CentralEGA completed queue

- [x] Upload 2 files encrypted with same session key<br/>
	  Expected outcome: Message in the CentralEGA user-error queue for the second file

- [x] (skipped) Use 2 stable IDs for the same ingested file<br/>
      Expected outcome: Error captured (where?)

- [x] Ingest a file with a user that does not exist in CentralEGA<br/>
      Expected outcome: Authentication "fails", and the ingestion does not start

- [x] Ingest a file with a user in CentralEGA, using the wrong password<br/>
      Expected outcome: Authentication "fails", and the ingestion does not start

- [x] Ingest a file with a user in CentralEGA, using the wrong sshkey<br/>
      Expected outcome: Fallback to password (previous scenario)

- [x] Ingest a file for a given LocalEGA using the key of another one<br/>
      Expected outcome: Message in the CentralEGA error queue, with the relevant content.

- [x] Ingestion with wrong file format<br/>
      Expected outcome: Message in the CentralEGA error queue, with the relevant content.

- [ ] Outgesting a cleartext file<br/>
      Expected outcome: Matching the original input file
	  Note: Insecure, we should not support that

- [ ] Outgesting a cleartext file, with a range<br/>
      Expected outcome: Matching the relevant part of the original input file

- [ ] Outgesting a C4GH-formatted file<br/>
      Expected outcome: Decrypt and match the original input file

## Robustness Tests

These tests will not treat the system as a black box.  
They require some knowledge on how the components are interconnected.

      $ bats tests/robustness

- [ ] Check Archive+DB consistency<br/>
      Expected outcome: Re-checksums the files after several ingestions

- [x] DB restarted after *n* seconds<br/>
      Expected outcome: Combining an ingestion before and one after, the latest one should still "work"

- [x] DB restarted in the middle of an ingestion<br/>
      Expected outcome: File ingested as usual

- [x] MQ restarted, test delivery mode<br/>
      Expected outcome: queued tasks completed

- [x] Central MQ restarted while LocalEGA shoveling the completion message<br/>
      Expected outcome: queued tasks completed

- [ ] Retry message 3 times if rejected before error or timeout<br/>
      Expected outcome: queued tasks completed

- [x] Restart all components in between 2 ingestions<br/>
      Expected outcome: Business as usual

## Stress

These tests treat the system as a black box and "measure" performance

      $ bats tests/stress

- [ ] Multiple ingestions by the same user<br/>
      Expected outcome: 

- [ ] Ingestions by multiple users<br/>
      Expected outcome: 

- [ ] (Auto?)-Scaling<br/>
       Expected outcome: 
  
## Security

These tests will not treat the system as a black box.  
They require some knowledge on how the components are interconnected.

      $ bats tests/security

- [ ] Network access forbidden from some selected components<br/>
      Expected outcome: 
  
- [x] Inbox user isolation: A user cannot access the files of another user<br/>
      Expected outcome: File not found or access denied

- [x] Database not reachable from the vault (only if S3-backed)<br/>
      Expected outcome: ping "db" fails from archive

- [x] Database not reachable from the inbox<br/>
      Expected outcome: ping "db" fails from inbox

- [x] Vault not reachable from the db (only if S3-backed)<br/>
      Expected outcome: ping "archive" fails from db

- [x] Vault not reachable from the inbox (only if S3-backed)<br/>
      Expected outcome: ping "archive" fails from inbox


