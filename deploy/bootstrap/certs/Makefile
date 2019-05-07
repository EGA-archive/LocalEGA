OPENSSL=~/.local/openssl/bin/openssl

SUBJ_PREFIX=/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA
DOMAIN=.localega
DOMAIN_EMAIL=-dev.ega@crg.eu

.PHONY: prepare

all: data/ingest.cert.pem \
     data/verify.cert.pem \
     data/finalize.cert.pem \
     data/db.cert.pem \
     data/mq.cert.pem \
     data/keys.cert.pem \
     data/inbox.cert.pem \
     data/archive.cert.pem \
     data/inbox-s3-backend.cert.pem 

cega: data/cega-mq.cert.pem \
      data/cega-users.cert.pem

prepare:
	@mkdir -p data
	@touch data/index.txt data/index.txt.attr
	@[[ -e data/serial ]] || echo 1000 > data/serial

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

data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem: data/CA.cert.pem
data/db.cert.pem data/mq.cert.pem data/inbox.cert.pem data/archive.cert.pem: data/CA.cert.pem
data/inbox-s3-backend.cert.pem data/keys.cert.pem: data/CA.cert.pem
data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem: EXT=client_cert
data/mq.cert.pem: EXT=server_client_cert
data/db.cert.pem data/inbox.cert.pem data/archive.cert.pem: EXT=server_cert
data/inbox-s3-backend.cert.pem data/keys.cert.pem: EXT=server_client_cert
data/cega-mq.cert.pem data/cega-users.cert.pem: EXT=server_cert
data/ingest.cert.pem data/verify.cert.pem data/finalize.cert.pem data/db.cert.pem data/mq.cert.pem data/inbox.cert.pem data/archive.cert.pem data/inbox-s3-backend.cert.pem data/keys.cert.pem data/cega-mq.cert.pem data/cega-users.cert.pem:
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
data/finalize.csr.pem: data/verify.sec.pem
data/db.csr.pem: data/db.sec.pem
data/mq.csr.pem: data/mq.sec.pem
data/inbox.csr.pem: data/inbox.sec.pem
data/keys.csr.pem: data/verify.sec.pem

data/cega-mq.csr.pem: data/cega-mq.sec.pem
data/cega-users.csr.pem: data/cega-users.sec.pem

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

data/ingest.csr.pem data/verify.csr.pem data/finalize.csr.pem: data/CA.sec.pem
data/db.csr.pem data/mq.csr.pem data/inbox.csr.pem data/archive.csr.pem: data/CA.sec.pem
data/inbox-s3-backend.csr.pem data/keys.csr.pem: data/CA.sec.pem
data/cega-mq.csr.pem data/cega-users.csr.pem: data/CA.sec.pem
data/ingest.csr.pem data/verify.csr.pem data/finalize.csr.pem data/db.csr.pem data/mq.csr.pem data/inbox.csr.pem data/archive.csr.pem data/inbox-s3-backend.csr.pem data/keys.csr.pem data/cega-mq.csr.pem data/cega-users.csr.pem:
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

###############################################
## Debug / Testing
###############################################

client-debug: DEBUG=-showcerts -prexit -state -debug -msg -tlsextdebug
client client-debug: data/ingest.cert.pem data/ingest.sec.pem data/CA.cert.pem
	$(OPENSSL) s_client -connect localhost:10000 -cert data/ingest.cert.pem -CAfile data/CA.cert.pem -key data/ingest.sec.pem -no_ssl3 -no_tls1 -noservername $(DEBUG)

server-debug: DEBUG=-msg -tlsextdebug -debug #-HTTP -www
server server-debug: data/db.cert.pem data/db.sec.pem data/CA.cert.pem
	$(OPENSSL) s_server -cert data/db.cert.pem -CAfile data/CA.cert.pem -key data/db.sec.pem -accept 10000 -no_ssl3 -no_tls1 -verify 10 $(DEBUG)
