## Testing script

This is used to simulate an upload and a submission from an end-user.

Run the script with

```
cd <this-directory>
make
```

Internally, it will:

1) create some fake user named `ega-box-999`, including its ssh-key.
2) Download the file `HG00458.unmapped.ILLUMINA.bwa.CHS.low_coverage.20130415.bam` from EBI.
3) Encrypt the file in the Crypt4GH format
4) Upload the encrypted file to the LocalEGA inbox
5) Trigger a fake submission on CentralEGA side

If all goes as expected, the CentralEGA (fake) message broker should
have received a message of completion.
