FROM centos:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y update && \
    yum -y install gcc git curl wget make \
		   nss-tools nc nmap tcpdump lsof \
		   rsyslog

COPY ega.conf /etc/rsyslog.d/ega.conf
#ENTRYPOINT ["rsyslogd", "-n", "-f", "/etc/rsyslogd.conf"]
