FROM gpg:2.1
LABEL maintainer "Frédéric Haziza, NBIS"

##############################################################
# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

COPY sshd_config /etc/ssh/sshd_config
COPY remote-gpg.sh /usr/local/bin/remote-gpg.sh
EXPOSE 22

# Cleaning the previous gpg keys
RUN rm -rf /root/{.gnupg,.ssh} && \
    mkdir -p /root/{.gnupg,.ssh} && \
    chmod 700 /root/{.gnupg,.ssh}

WORKDIR /root/.gnupg
COPY gpg.conf .
COPY gpg-agent.conf .

COPY ssh_config /root/.ssh/config

##############################################################
# Cleanup
RUN rm -rf /var/src/{gnupg,openssh}
WORKDIR /

