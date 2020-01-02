
SHELL := /bin/bash
OPENSSL := openssl
SUBJ_PREFIX := /C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA
# HOSTNAME_DOMAIN # defined in the including Makefile
DOMAIN_EMAIL := -dev.ega@crg.eu

.PHONY: all-certs prepare-certs clean-certs cega-certs

COMPONENTS=ingest \
           verify \
           finalize \
           db \
           mq \
           keys \
           inbox \
	   outgest \
	   streamer

ifdef S3
COMPONENTS+=archive inbox-s3-backend
endif

CEGA_COMPONENTS=cega-mq cega-users

ALL_COMPONENTS=$(COMPONENTS) $(CEGA_COMPONENTS) testsuite

.PRECIOUS: $(OPENSSL_DBs)                                 \
	   $(ALL_COMPONENTS:%=../private/certs/%.sec.pem) \
	   $(ALL_COMPONENTS:%=../private/certs/%.csr.pem)

#.INTERMEDIATE: ../private/certs/*.csr.pem

all-certs: prepare-certs \
	   $(COMPONENTS:%=../private/certs/%.cert.pem) \
	   $(COMPONENTS:%=../private/certs/CA.%.cert.pem)
	@chmod 444 $(COMPONENTS:%=../private/certs/%.sec.pem)

testsuite-certs: prepare-certs \
	   	 ../private/certs/testsuite.cert.pem \
	         ../private/certs/CA.testsuite.cert.pem

cega-certs: prepare-certs \
	   $(CEGA_COMPONENTS:%=../private/certs/%.cert.pem) \
	   $(CEGA_COMPONENTS:%=../private/certs/CA.%.cert.pem)
	@chmod 444 $(CEGA_COMPONENTS:%=../private/certs/%.sec.pem)

###############################################
## Necessary files
###############################################

# We add a separate rules and not a dependency,
# because these files will change for each created certificate
# and we don't want to re-create *.cert.pem for that
prepare-certs:
	@mkdir -p ../private/certs
	@touch ../private/certs/index.txt
	@touch ../private/certs/index.txt.attr
	@test -e ../private/certs/serial || echo 1000 > ../private/certs/serial


###############################################
## Root CA Certificates
###############################################

../private/certs/CA.cert.pem: ../private/certs/CA.sec.pem
	@echo "Creating $(@F)"
	@mkdir -p $(@D) 
	@$(OPENSSL) req -config certs.cnf \
	           -subj "/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA/CN=LocalEGA root CA/emailAddress=dev.ega@crg.eu" \
	           -key $< -x509 -new -days 7300 -sha256 -nodes \
	           -extensions v3_ca -out $@


###############################################
## Certificates
###############################################

../private/certs/ingest.cert.pem: EXT=client_cert
../private/certs/verify.cert.pem: EXT=client_cert
../private/certs/finalize.cert.pem: EXT=client_cert
../private/certs/mq.cert.pem: EXT=server_client_cert
../private/certs/inbox.cert.pem: EXT=server_client_cert
../private/certs/db.cert.pem: EXT=server_cert
../private/certs/keys.cert.pem: EXT=server_cert
../private/certs/cega-mq.cert.pem: EXT=server_cert
../private/certs/cega-users.cert.pem: EXT=server_cert
../private/certs/outgest.cert.pem: EXT=server_client_cert
../private/certs/streamer.cert.pem: EXT=server_client_cert
../private/certs/testsuite.cert.pem: EXT=client_cert

ifdef S3
../private/certs/archive.cert.pem: EXT=server_cert
../private/certs/inbox-s3-backend.cert.pem: EXT=server_cert
endif

%.cert.pem: %.csr.pem
	@echo "Creating $(@F)"
	@$(OPENSSL) ca -config certs.cnf \
	           -extensions $(EXT) \
	           -days 375 -notext -md sha256 -in $< -out $@
#	-@rm ../private/certs/100*.pem

###############################################
## CSR - Certificate Signing Request
###############################################

%.csr.pem: %.sec.pem ../private/certs/CA.cert.pem
	@echo "Creating $(@F)"
	@$(OPENSSL) req -config certs.cnf \
	           -subj "${SUBJ_PREFIX}/CN=$(@:../private/certs/%.csr.pem=%)${HOSTNAME_DOMAIN}/emailAddress=$(@:../private/certs/%.csr.pem=%)${DOMAIN_EMAIL}" \
	           -key $< -new -sha256 -out $@


###############################################
## Private keys
###############################################
../private/certs/%.sec.pem:
	@echo "Creating $(@F)"
	@mkdir -p $(@D) 
	@$(OPENSSL) genpkey -algorithm RSA -out $@
	@chmod 400 $@

###############################################
## Misc
###############################################

clean-certs:
	@rm -rf ../private/certs

../private/certs/CA.%.cert.pem: ../private/certs/CA.cert.pem
	@echo -e "\t$(<F) > $(@F)"
	@cp $< $@
