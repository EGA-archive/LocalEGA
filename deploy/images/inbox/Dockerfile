FROM egarchive/base
LABEL maintainer "EGA System Developers"

RUN groupadd -r lega && \
    useradd -M -r -g lega lega

EXPOSE 9000
VOLUME /ega/inbox

RUN yum -y install autoconf patch openssl-devel pam-devel libcurl-devel nss-tools readline-devel libedit-devel
#    	   	   nc nmap tcpdump lsof strace bash-completion bash-completion-extras

##
## Install SQLite 3.24
##
ARG SQLITE_VERSION=3240000
RUN cd && wget https://sqlite.org/2018/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    cd sqlite-autoconf-${SQLITE_VERSION} && \
    ./configure && \
    make && make install && \
    echo '/usr/local/lib' >> /etc/ld.so.conf.d/ega.conf && \
    cd && rm -rf sqlite-autoconf-${SQLITE_VERSION}{,.tar.gz}

RUN git clone https://github.com/EGA-archive/EGA-auth.git /root/ega-auth && \
    mkdir -p /usr/local/lib/ega && \
    cd /root/ega-auth/src && \
    make install clean && \
    echo '/usr/local/lib/ega' >> /etc/ld.so.conf.d/ega.conf && \
    echo 'Welcome to Local EGA' > /ega/banner && \
    cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf && \
    cd && rm -rf /root/ega-auth

RUN ldconfig -v

ARG OPENSSH_DIR=/opt/openssh
ARG SSHD_UID=74
ARG SSHD_GID=74
ARG OPENSSH_TAG=V_7_8_P1

RUN getent group ssh_keys >/dev/null || groupadd -r ssh_keys || :
RUN getent group sshd || groupadd -g ${SSHD_GID} -r sshd

# RUN mkdir -p /var/empty && \
#     useradd -c "Privilege-separated SSH" \
#             -u ${SSHD_UID} \
# 	    -g sshd \
# 	    -s /sbin/nologin \
# 	    -r \
# 	    -m -d /var/empty/sshd sshd
#### Weird.... useradd does segfault.

RUN sed -i -e '/sshd/ d' /etc/passwd && \
    echo "sshd:x:${SSHD_UID}:${SSHD_GID}:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin" >> /etc/passwd && \
    mkdir -p /var/empty/sshd && chmod 700 /var/empty/sshd

RUN git clone --branch ${OPENSSH_TAG} git://anongit.mindrot.org/openssh.git /root/openssh && \
    cd /root/openssh && \
    autoreconf && \
    ./configure \
        --prefix=${OPENSSH_DIR} \
	--with-privsep-path=/var/empty/sshd \
        --with-privsep-user=sshd \
        --with-ssl-engine \
	--disable-strip \
	--without-smartcard \
        --with-pam \
        --without-selinux \
	--without-kerberos5 \
        --with-libedit

COPY notify_cega.patch /root/openssh/notify_cega.patch

RUN cd /root/openssh && \
    patch -p0 < notify_cega.patch && \
    make && make install

RUN rm -f /etc/ssh/ssh_host_{rsa,dsa,ecdsa,ed25519}_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

RUN rm -rf /root/openssh && \
    cp ${OPENSSH_DIR}/sbin/sshd ${OPENSSH_DIR}/sbin/ega

# Install the notification system

# These are enough
RUN pip3.6 install pika==0.12.0 uvloop

ARG checkout=master
# RUN pip3.6 install git+https://github.com/EGA-archive/LocalEGA.git@${checkout}
RUN git clone https://github.com/ega-archive/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout} && cd && \
    pip3.6 install /root/LocalEGA && \
    rm -rf /root/LocalEGA
    
COPY banner /ega/banner
COPY pam.ega /etc/pam.d/ega
COPY sshd_config /etc/ega/sshd_config

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
