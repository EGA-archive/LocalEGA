FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install openssh-server postgresql-devel pam-devel libcurl-devel jq-devel fuse fuse-libs cronie

##################################
EXPOSE 22
VOLUME /ega/inbox
ENV DB_INSTANCE=

##################################
# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key && \
    ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key && \
    useradd ega && \
    mkdir -p /usr/local/lib/ega && \
    echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf && \
    echo 'Welcome to Local EGA' > /ega/banner && \
    cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf && \
    git clone -b fuse https://github.com/NBISweden/LocalEGA-auth /root/ega-auth && \
    cd /root/ega-auth/src && \
    make debug clean && \
    ldconfig -v && \
    chown root:ega /ega/inbox && \
    chmod 750 /ega/inbox && \
    chmod g+s /ega/inbox && \
    mv /etc/pam.d/sshd /etc/pam.d/sshd.bak

ARG checkout=dev
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

COPY pam.ega /etc/pam.d/ega
COPY pam.sshd /etc/pam.d/sshd
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]

