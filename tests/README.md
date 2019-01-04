# LocalEGA testsuite

Unit Tests are run with pytest, coverage and tox.
The other tests use BATS.

## Integration Tests

* Ingesting a 10MB file<br/>
  Expected outcome: Message in the CentralEGA completed queue
  
* Ingesting a "big" file<br/>
  Expected outcome: Message in the CentralEGA completed queue

* Ingesting a directory with multiple files and/or subdirectories<br/>
  Expected outcome: Messages in the CentralEGA completed queue

* Upload 2 files encrypted with same session key<br/>
  Expected outcome: Message in the CentralEGA user-error queue for the second file

* Use 2 stable IDs for the same ingested file<br/>
  Expected outcome: Error captured (where?)

* Ingest a file with a user that does not exist in CentralEGA<br/>
  Expected outcome: Authentication "fails", and the ingestion does not start

* Ingest a file with a user in CentralEGA, using the wrong password<br/>
  Expected outcome: Authentication "fails", and the ingestion does not start

* Ingest a file with a user in CentralEGA, using the wrong sshkey<br/>
  Expected outcome: Fallback to password (previous scenario)

* Ingest a file for a given LocalEGA using the key of another one<br/>
  Expected outcome: Message in the CentralEGA error queue, with the relevant content.

* Ingestion with wrong file format<br/>
  Expected outcome: Message in the CentralEGA error queue, with the relevant content.

* Outgesting a cleartext file<br/>
  Expected outcome: Matching the original input file

* Outgesting a cleartext file, with a range<br/>
  Expected outcome: Matching the relevant part of the original input file

* Outgesting a C4GH-formatted file<br/>
  Expected outcome: Decrypt and match the original input file

* Check Vault+DB consistency<br/>
  Expected outcome: Re-checksums the files after several ingestions

## Robustness Tests

* DB restarted after *n* seconds<br/>
  Expected outcome: Combining an ingestion before and one after, the latest one should still "work"

* DB restarted in the middle of an ingestion<br/>
  Expected outcome: File ingested as usual

* MQ restarted, test delivery mode<br/>
  Expected outcome: queued tasks completed

* Retry message 3 times if rejected before error or timeout<br/>
  Expected outcome: queued tasks completed

* Restart some component X<br/>
  Expected outcome: Business as usual

## Stress

* Multiple ingestions by the same user<br/>
  Expected outcome: 

* Ingestions by multiple users<br/>
  Expected outcome: 

* (Auto?)-Scaling<br/>
  Expected outcome: 
  
## Security

* Network access forbidden from some selected components<br/>
  Expected outcome: 
  
* Inbox user isolation: When I'm logged as John, I can not look at the files of Jane.<br/>
  Expected outcome: 


