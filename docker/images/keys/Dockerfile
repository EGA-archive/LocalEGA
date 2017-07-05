FROM gpg:2.1
LABEL maintainer "Frédéric Haziza, NBIS"

##############################################################
# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

EXPOSE 22

##############################################################
COPY sshd_config    /etc/ssh/sshd_config
COPY ssh_config     /root/.ssh/config
COPY remote-gpg.sh  /usr/local/bin/remote-gpg.sh
RUN  chmod +x /usr/local/bin/remote-gpg.sh

VOLUME /root/.gnupg
