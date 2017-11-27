FROM centos:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum install -y epel-release && \
    yum -y update && \
    yum -y install gcc git make rsyslog \
		   openssh-server \
		   nss-tools nc nmap tcpdump lsof strace \
	       	   bash-completion bash-completion-extras \
		   postgresql-devel pam-devel libcurl-devel jq-devel

##################################
RUN mkdir -p /usr/local/lib/ega
COPY ega.ld.conf /etc/ld.so.conf.d/ega.conf

##################################
RUN mkdir -p /var/run/sshd
EXPOSE 22

# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key && \
    ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key 

##################################
COPY pam.ega /etc/pam.d/ega
RUN mv /etc/pam.d/sshd /etc/pam.d/sshd.bak
COPY pam.sshd /etc/pam.d/sshd

RUN cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf

COPY banner /ega/banner
COPY sshd_config /etc/ssh/sshd_config

ARG checkout=dev

RUN git clone https://github.com/NBISweden/LocalEGA /root/ega && \
    cd /root/ega && \
    git checkout ${checkout} && \
    cd src/auth && \
    make install clean && \
    ldconfig -v

RUN useradd ega
VOLUME /ega/inbox

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
ENV DB_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
