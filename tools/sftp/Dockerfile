FROM centos:latest
MAINTAINER Frédéric Haziza, NBIS

RUN yum -y install openssh-server

RUN mkdir -p /var/run/sshd
RUN groupadd --system sftp_users

COPY sshd_config /etc/ssh/sshd_config

COPY useradd_defaults /etc/default/useradd

#RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key
#COPY add_inbox_user.sh /usr/local/bin/

EXPOSE 22

ENTRYPOINT ["/usr/sbin/sshd","-D", "-e"]
