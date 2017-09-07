FROM nbis/ega:common
LABEL maintainer "Frédéric Haziza, NBIS"

# Clean from ega-common
RUN rm -rf /ega/{vault,staging}

RUN pip install pika==0.10.0 aiopg==0.13.0

RUN yum -y install postgresql-devel automake autoconf libtool libgcrypt libgcrypt-devel pam-devel
RUN git clone https://github.com/pam-pgsql/pam-pgsql.git ~/pam-pgsql

##################################
# For SFTP
##################################
RUN mkdir -p /var/run/sshd
EXPOSE 22

# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

RUN rm -rf /ega/skel && \
    mkdir -p /ega/skel/inbox && \
    chmod 750 /ega/skel && \
    chmod 770 /ega/skel/inbox && \
    chmod g+s /ega/skel/inbox # rwxrws---


COPY sshd_config /etc/ssh/sshd_config
COPY ega-ssh-keys.sh /usr/local/bin/ega-ssh-keys.sh
COPY banner /ega/banner

##################################
# For PAM and NSS
##################################
RUN mkdir -p /usr/local/lib/ega
COPY ega.ld.conf /etc/ld.so.conf.d/ega.conf
COPY ega_homedir.sh /usr/local/bin/ega_homedir.sh

RUN cp /etc/pam.d/sshd /etc/pam.d/sshd.bak
COPY pam.ega /etc/pam.d/ega
COPY pam.sshd /etc/pam.d/sshd
COPY pam.pgsql.conf /etc/pam_pgsql.conf

RUN pushd ~/pam-pgsql && \
    ./autogen.sh && \
    ./configure --libdir=/usr/local/lib/ega && \
    make && \
    make install && \
    ldconfig -v && \
    popd

RUN cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1ega files/' /etc/nsswitch.conf && \
    sed -i -e 's/^shadow:\(.*\)files/shadow:\1ega files/' /etc/nsswitch.conf

