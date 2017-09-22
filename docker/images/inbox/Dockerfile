FROM nbis/ega:common
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install postgresql-devel pam-devel libcurl-devel json-c-devel

##################################
RUN mkdir -p /usr/local/lib/ega
COPY ega.ld.conf /etc/ld.so.conf.d/ega.conf

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


##################################
COPY ega_homedir.sh /usr/local/bin/ega_homedir.sh
COPY pam.ega /etc/pam.d/ega
RUN mv /etc/pam.d/sshd /etc/pam.d/sshd.bak
COPY pam.sshd /etc/pam.d/sshd

RUN cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf

COPY sshd_config /etc/ssh/sshd_config
COPY ega_ssh_keys.sh /usr/local/bin/ega_ssh_keys.sh
RUN chmod 755 /usr/local/bin/ega_ssh_keys.sh
COPY banner /ega/banner

RUN useradd ega

VOLUME /ega/inbox
