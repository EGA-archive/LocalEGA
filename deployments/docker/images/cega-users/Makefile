# DOCUMENTATION: https://jamielinux.com/docs/openssl-certificate-authority/index.html

.PHONY: show_root_cert show_cega_csr show_lega_csr prepare clean

CA_PASSWORD=hello
CA_SUBJ=/C=SE/ST=Sweden/L=Uppsala/O=NBIS/OU=SysDevs-CA/CN=EGA-CA/emailAddress=ega-ca@nbis.se

CEGA_PASSWORD=hello
#CEGA_SUBJ=/C=ES/ST=Catalunya/L=Barcelona/O=EGA/OU=SysDevs/CN=EGA/emailAddress=ega@crg.eu
CEGA_SUBJ=/C=SE/ST=Sweden/L=Uppsala/O=NBIS/OU=SysDevs/CN=CEGA/emailAddress=ega@nbis.se

LEGA_PASSWORD=hello
LEGA_SUBJ=/C=SE/ST=Sweden/L=Uppsala/O=NBIS/OU=SysDevs/CN=LocalEGA/emailAddress=ega@nbis.se

all: prepare verify

certs:
	mkdir $@
csr:
	mkdir $@
newcerts:
	mkdir $@
private:
	mkdir $@
index.txt:
	touch $@
serial:
	echo '1000' > $@

prepare: certs csr newcerts index.txt private serial

########## CA
private/ca.key.pem: private prepare
	rm -f $@
	openssl genrsa -aes256 -out $@ -passout pass:${CA_PASSWORD} 4096
	chmod 400 $@

certs/ca.cert.pem: private/ca.key.pem openssl.cnf certs
	rm -f $@
	openssl req -config openssl.cnf -key $< -new -x509 -days 7300 -sha256 -extensions v3_ca -subj ${CA_SUBJ} -out $@ -passin pass:${CA_PASSWORD}
	chmod 444 $@

show_root_cert: certs/ca.cert.pem
	openssl x509 -noout -text -in $<


########## CEGA
private/cega.key.pem: private
	openssl genrsa -aes256 -out $@ -passout pass:${CEGA_PASSWORD} 2048

csr/cega.csr.pem: private/cega.key.pem openssl.cnf private/ca.key.pem
	openssl req -config openssl.cnf -key $< -new -sha256 -subj ${CEGA_SUBJ} -out $@ -passin pass:${CEGA_PASSWORD}

certs/cega.cert.pem: csr/cega.csr.pem certs/ca.cert.pem
	openssl ca -batch -config openssl.cnf -extensions server_cert -days 375 -notext -md sha256 -in $< -out $@ -passin pass:${CEGA_PASSWORD}

show_cega_csr: certs/cega.cert.pem
	openssl x509 -noout -text -in $<

########## LEGA SWEDEN
private/lega.sweden.key.pem: private
	openssl genrsa -aes256 -out $@ -passout pass:${LEGA_PASSWORD} 2048

csr/lega.sweden.csr.pem: private/lega.sweden.key.pem openssl.cnf private/ca.key.pem
	openssl req -config openssl.cnf -key $< -new -sha256 -subj ${LEGA_SUBJ} -out $@ -passin pass:${LEGA_PASSWORD}

certs/lega.sweden.cert.pem: csr/lega.sweden.csr.pem certs/ca.cert.pem
	openssl ca -batch -config openssl.cnf -extensions server_cert -days 375 -notext -md sha256 -in $< -out $@ -passin pass:${LEGA_PASSWORD}

show_lega_csr: certs/lega.sweden.cert.pem
	openssl x509 -noout -text -in $<

verify: certs/ca.cert.pem certs/lega.sweden.cert.pem certs/cega.cert.pem
	openssl verify -CAfile certs/ca.cert.pem certs/lega.sweden.cert.pem
	openssl verify -CAfile certs/ca.cert.pem certs/cega.cert.pem

clean:
	rm -rf certs csr newcerts private
	rm -f serial serial* index.txt*

connect: prepare verify
	openssl s_client -connect ega_frontend:9100 -CAfile certs/ca.cert.pem
