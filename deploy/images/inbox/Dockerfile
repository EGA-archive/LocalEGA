FROM centos:7.5.1804
LABEL maintainer "EGA System Developers"

EXPOSE 9000
VOLUME /ega/inbox

# Before the EGA PAM lib is loaded
RUN groupadd -r lega && \
    useradd -r -g lega lega

#################################################
##
## Upgrade CentOS 7, and install Python 3.6
##
#################################################

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y install epel-release && \
    yum -y update && \
    yum -y install git gcc make bzip2 curl \
                   zlib-devel bzip2-devel unzip \
		   wget dpkg \
                   openssl openssl-devel \
		   autoconf patch pam-devel libcurl-devel nss-tools readline-devel libedit-devel \
		   python36u python36u-devel python36u-pip

# Adding the DEV packages?
# RUN yum install -y nss-tools nc nmap tcpdump lsof strace bash-completion bash-completion-extras

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

#################################################
##
## Install SQLite 3.26
##
#################################################

ARG SQLITE_VERSION=3260000

RUN cd && wget https://sqlite.org/2018/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    cd sqlite-autoconf-${SQLITE_VERSION} && \
    ./configure && \
    make && make install && \
    echo '/usr/local/lib' >> /etc/ld.so.conf.d/ega.conf && \
    cd && rm -rf sqlite-autoconf-${SQLITE_VERSION}{,.tar.gz}

#################################################
##
## Install OpenSSH (and patch it)
##
#################################################

ARG OPENSSH_DIR=/opt/openssh
ARG SSHD_UID=74
ARG SSHD_GID=74
ARG OPENSSH_TAG=V_7_8_P1

RUN getent group ssh_keys >/dev/null || groupadd -r ssh_keys || :
RUN getent group sshd || groupadd -g ${SSHD_GID} -r sshd

RUN mkdir -p /var/empty/sshd && \
    chmod 700 /var/empty/sshd && \
    useradd -c "Privilege-separated SSH" \
            -u ${SSHD_UID} \
	    -g sshd \
	    -s /sbin/nologin \
	    -r \
	    -d /var/empty/sshd sshd
# /var/empty/sshd must be owned by root and not group or world-writable.

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

RUN rm -f /etc/ssh/ssh_host_{rsa,dsa,ed25519}_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

RUN rm -rf /root/openssh && \
    cp ${OPENSSH_DIR}/sbin/sshd ${OPENSSH_DIR}/sbin/ega

COPY banner /ega/banner
COPY sshd_config /etc/ega/sshd_config

#################################################
##
## Install EGA PAM
##
#################################################

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

COPY pam.ega /etc/pam.d/ega

#################################################
##
## Install GOSU
##
#################################################

ENV GOSU_VERSION 1.10
ENV GPG_KEYS B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN set -ex && \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}" && \
    wget -O /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}.asc"

# verify the signature
RUN export GNUPGHOME="$(mktemp -d)" && \
    (gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEYS" \
    || gpg --keyserver pgp.mit.edu --recv-keys "$GPG_KEYS" \
    || gpg --keyserver keyserver.pgp.com --recv-keys "$GPG_KEYS") && \
    gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-keys  && \
    gpg --batch --verify /tmp/gosu.asc /usr/bin/gosu && \
    rm -r "$GNUPGHOME" /tmp/gosu.asc && \
    chmod +x /usr/bin/gosu

# verify that the binary works
RUN gosu nobody true

#################################################
##
## Install the notification system
##
#################################################

# These are enough
RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml pika==0.12.0 uvloop

ARG checkout=master
RUN git clone https://github.com/ega-archive/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout} && cd && \
    pip3.6 install /root/LocalEGA && \
    rm -rf /root/LocalEGA
    

#################################################
##
## Clean up
##
#################################################
RUN yum -y remove dpkg && \
    yum clean all && \
    rm -rf /var/cache/yum

#################################################

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
