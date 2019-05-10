
SHELL := /bin/bash
OPENSSL := ${OPENSSL:-openssl}
SUBJ_PREFIX := /C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA
#DOMAIN := .localega
DOMAIN_EMAIL := -dev.ega@crg.eu

.PHONY: all prepare clean cega

all: data/ingest.cert.pem \
     data/verify.cert.pem \
     data/finalize.cert.pem \
     data/db.cert.pem \
     data/mq.cert.pem \
     data/keys.cert.pem \
     data/inbox.cert.pem \
     data/archive.cert.pem \
     data/inbox-s3-backend.cert.pem

testsuite: data/testsuite.cert.pem

cega: data/cega-mq.cert.pem \
      data/cega-users.cert.pem

data-out: data/outgest.cert.pem \
	  data/streamer.cert.pem

prepare:
	@mkdir -p data
	@touch data/index.txt data/index.txt.attr
	@test -e data/serial || echo 1000 > data/serial


###############################################
## Root CA Certificates
###############################################

data/CA.cert.pem: data/CA.sec.pem
	@echo "======== Creating $@"
	@$(OPENSSL) req -config LocalEGA.cnf \
	           -subj "/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA/CN=LocalEGA root CA/emailAddress=dev.ega@crg.eu" \
	           -key $< -x509 -new -days 7300 -sha256 -nodes \
	           -extensions v3_ca -out $@


###############################################
## Certificates
###############################################

data/ingest.cert.pem: data/ingest.csr.pem 
data/verify.cert.pem: data/verify.csr.pem
data/finalize.cert.pem: data/finalize.csr.pem

data/db.cert.pem: data/db.csr.pem
data/mq.cert.pem: data/mq.csr.pem
data/inbox.cert.pem: data/inbox.csr.pem
data/archive.cert.pem: data/archive.csr.pem
data/inbox-s3-backend.cert.pem: data/inbox-s3-backend.csr.pem
data/keys.cert.pem: data/keys.csr.pem

data/cega-mq.cert.pem: data/cega-mq.csr.pem
data/cega-users.cert.pem: data/cega-users.csr.pem

data/outgest.cert.pem: data/outgest.csr.pem
data/streamer.cert.pem: data/streamer.csr.pem

data/testsuite.cert.pem: data/testsuite.csr.pem

data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem: data/CA.cert.pem
data/db.cert.pem data/mq.cert.pem data/inbox.cert.pem data/archive.cert.pem: data/CA.cert.pem
data/inbox-s3-backend.cert.pem data/keys.cert.pem: data/CA.cert.pem
data/cega-mq.cert.pem data/cega-users.cert.pem: data/CA.cert.pem
data/outgest.cert.pem data/streamer.cert.pem: data/CA.cert.pem
data/testsuite.cert.pem: data/CA.cert.pem

data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem: EXT=client_cert
data/mq.cert.pem data/inbox.cert.pem: EXT=server_client_cert
data/db.cert.pem data/archive.cert.pem: EXT=server_cert
data/inbox-s3-backend.cert.pem data/keys.cert.pem: EXT=server_cert
data/cega-mq.cert.pem data/cega-users.cert.pem: EXT=server_cert
data/outgest.cert.pem data/streamer.cert.pem: EXT=server_client_cert
data/testsuite.cert.pem: EXT=client_cert
data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem data/db.cert.pem data/mq.cert.pem data/inbox.cert.pem data/archive.cert.pem data/inbox-s3-backend.cert.pem data/keys.cert.pem data/cega-mq.cert.pem data/cega-users.cert.pem data/outgest.cert.pem data/streamer.cert.pem data/testsuite.cert.pem:
	@echo "======== Creating $@"
	@$(OPENSSL) ca -config LocalEGA.cnf \
	           -extensions $(EXT) \
	           -days 375 -notext -md sha256 -in $< -out $@
	-@rm data/100*.pem


###############################################
## CSR - Certificate Signing Request
###############################################

data/ingest.csr.pem: data/ingest.sec.pem
data/verify.csr.pem: data/verify.sec.pem
data/finalize.csr.pem: data/finalize.sec.pem
data/db.csr.pem: data/db.sec.pem
data/mq.csr.pem: data/mq.sec.pem
data/inbox.csr.pem: data/inbox.sec.pem
data/keys.csr.pem: data/keys.sec.pem
data/archive.csr.pem: data/archive.sec.pem
data/inbox-s3-backend.csr.pem: data/inbox-s3-backend.sec.pem

data/cega-mq.csr.pem: data/cega-mq.sec.pem
data/cega-users.csr.pem: data/cega-users.sec.pem

data/outgest.csr.pem: data/outgest.sec.pem
data/streamer.csr.pem: data/streamer.sec.pem

data/testsuite.csr.pem: data/testsuite.sec.pem

data/ingest.csr.pem: COMPONENT=ingest
data/verify.csr.pem: COMPONENT=verify
data/finalize.csr.pem: COMPONENT=finalize
data/db.csr.pem: COMPONENT=db
data/mq.csr.pem: COMPONENT=mq
data/inbox.csr.pem: COMPONENT=inbox
data/keys.csr.pem: COMPONENT=keys
data/archive.csr.pem: COMPONENT=archive
data/inbox-s3-backend.csr.pem: COMPONENT=inbox-s3-backend

data/cega-mq.csr.pem: COMPONENT=cega-mq
data/cega-users.csr.pem: COMPONENT=cega-users

data/outgest.csr.pem: COMPONENT=outgest
data/streamer.csr.pem: COMPONENT=streamer

data/testsuite.csr.pem: COMPONENT=testsuite

data/ingest.csr.pem data/verify.csr.pem data/finalize.csr.pem: data/CA.sec.pem
data/db.csr.pem data/mq.csr.pem data/inbox.csr.pem data/archive.csr.pem: data/CA.sec.pem
data/inbox-s3-backend.csr.pem data/keys.csr.pem: data/CA.sec.pem
data/cega-mq.csr.pem data/cega-users.csr.pem: data/CA.sec.pem
data/outgest.csr.pem data/streamer.csr.pem: data/CA.sec.pem
data/testsuite.csr.pem: data/CA.sec.pem
data/ingest.csr.pem data/verify.csr.pem data/finalize.csr.pem data/db.csr.pem data/mq.csr.pem data/inbox.csr.pem data/archive.csr.pem data/inbox-s3-backend.csr.pem data/keys.csr.pem data/cega-mq.csr.pem data/cega-users.csr.pem data/outgest.csr.pem data/streamer.csr.pem data/testsuite.csr.pem:
	@echo "======== Creating $@"
	@$(OPENSSL) req -config LocalEGA.cnf \
	           -subj "${SUBJ_PREFIX}/CN=${COMPONENT}${DOMAIN}/emailAddress=${COMPONENT}${DOMAIN_EMAIL}" \
	           -key $< -new -sha256 -out $@


###############################################
## Private keys
###############################################
data/%.sec.pem:
	@echo "======== Creating $@"
	@$(OPENSSL) genpkey -algorithm RSA -out $@
	@chmod 400 $@

###############################################
## Misc
###############################################

clean:
	@rm -rf data

