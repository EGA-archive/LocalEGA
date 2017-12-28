FROM centos:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum install -y epel-release && \
    yum -y update && \
    yum -y install gcc git curl make bzip2 unzip \
    	   	   openssl \
		   nss-tools nc nmap tcpdump lsof strace \
	       	   bash-completion bash-completion-extras \
		   python36u python36u-pip

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml Markdown pika aiohttp pycryptodomex aiopg colorama aiohttp-jinja2

