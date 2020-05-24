
SHELL := /bin/bash
OPENSSL := openssl
SUBJ_PREFIX := /C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA
# HOSTNAME_DOMAIN # defined in the including Makefile
DOMAIN_EMAIL := -dev.ega@crg.eu

###############################################
## Necessary files
###############################################

../private/certs:
	@mkdir -p $@

../private/certs/serial: | ../private/certs
	@echo '1000' > $@

../private/certs/index.txt: | ../private/certs
	@touch $@

###############################################
## Root CA Certificates
###############################################

../private/certs/CA.cert.pem: ../private/certs/CA.sec.pem | ../private/certs
	@echo "Creating $(@F)"
	@$(OPENSSL) req -config certs.cnf \
	           -subj "/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=EGA/CN=LocalEGA root CA/emailAddress=dev.ega@crg.eu" \
	           -key $< -x509 -new -days 7300 -sha256 -nodes \
	           -extensions v3_ca -out $@ 2>../private/.err


###############################################
## Certificates
###############################################

../private/certs/dispatcher.cert.pem: EXT=client_cert
../private/certs/ingest.cert.pem: EXT=client_cert
../private/certs/verify.cert.pem: EXT=client_cert
../private/certs/finalize.cert.pem: EXT=client_cert
../private/certs/mq.cert.pem: EXT=server_client_cert
../private/certs/inbox.cert.pem: EXT=server_client_cert
../private/certs/db.cert.pem: EXT=server_cert
../private/certs/keys.cert.pem: EXT=server_cert
../private/certs/cega-mq.cert.pem: EXT=server_cert
../private/certs/cega-users.cert.pem: EXT=server_cert
../private/certs/cega-accession.cert.pem: EXT=client_cert
../private/certs/outgest.cert.pem: EXT=server_client_cert
../private/certs/streamer.cert.pem: EXT=server_client_cert
../private/certs/testsuite.cert.pem: EXT=client_cert
../private/certs/archive-db.cert.pem: EXT=server_cert

ifdef S3
../private/certs/archive.cert.pem: EXT=server_cert
../private/certs/inbox-s3-backend.cert.pem: EXT=server_cert
endif

%.cert.pem: %.csr.pem | ../private/certs/serial ../private/certs/index.txt
	@echo "Creating $(@F)"
	@yes | $(OPENSSL) ca -config certs.cnf \
	           -extensions $(EXT) \
	           -days 375 -notext -md sha256 -in $< -out $@ 2>../private/.err
	-@rm ../private/certs/10*.pem

###############################################
## CSR - Certificate Signing Request
###############################################
# Uncomment if you want to keep the CSRs
# .PRECIOUS: %.csr.pem

%.csr.pem: %.sec.pem ../private/certs/CA.cert.pem | ../private/certs
	@echo "Creating $(@F)"
	@$(OPENSSL) req -config certs.cnf \
	           -subj "${SUBJ_PREFIX}/CN=$(@:../private/certs/%.csr.pem=%)${HOSTNAME_DOMAIN}/emailAddress=$(@:../private/certs/%.csr.pem=%)${DOMAIN_EMAIL}" \
	           -key $< -new -sha256 -out $@ 2>../private/.err


###############################################
## Private keys
###############################################
../private/certs/%.sec.pem: | ../private/certs
	@echo "Creating $(@F)"
	@$(OPENSSL) genpkey -algorithm RSA -out $@ 2>../private/.err
	@chmod 444 $@

# 444 instead of 400 to solve permission issues when docker-compose is injecting the files
# Normally not happening when using docker secrets

###############################################
## Misc
###############################################

.PHONY: clean-certs
clean-certs:
	rm -rf ../private/certs

../private/certs/CA.%.cert.pem: ../private/certs/CA.cert.pem
	@echo -e "\t$(<F) > $(@F)"
	@cp $< $@
