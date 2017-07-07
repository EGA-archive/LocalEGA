FROM ega:common
LABEL maintainer "Frédéric Haziza, NBIS"

# Clean from ega-common
RUN rm -rf /ega/{vault,staging}

RUN pip install pika==0.10.0 aiopg==0.13.0

##################################
# For SFTP
##################################
RUN mkdir -p /var/run/sshd
RUN groupadd --system sftp_users
COPY sshd_config /etc/ssh/sshd_config
COPY useradd_defaults /etc/default/useradd

EXPOSE 22

# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

RUN mkdir -p /etc/ssh/authorized_keys && \
    chmod 700 /etc/ssh/authorized_keys && \
    touch /etc/ssh/authorized_keys/root && \
    chmod 600 /etc/ssh/authorized_keys/root

RUN chown root:root /home
RUN chmod g+s /home

RUN rm -rf /etc/skel/.bash*
RUN mkdir -p /etc/skel/inbox && \
    chmod 700 /etc/skel/inbox
