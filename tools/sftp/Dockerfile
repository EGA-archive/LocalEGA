FROM centos:latest
MAINTAINER Frédéric Haziza, NBIS

RUN yum -y update
RUN yum -y install gcc git curl make zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl openssl-devel openssh-server nss-tools

##################################
# For Python 3.6.1, using PyEnv
##################################

ENV LANG C.UTF-8
ENV PYTHON_VERSION 3.6.1

RUN git clone git://github.com/yyuu/pyenv.git ~/.pyenv

RUN echo 'export PYENV_ROOT=$HOME/.pyenv' >> ~/.bash_profile
RUN echo 'export PATH=$PYENV_ROOT/bin:$PATH' >> ~/.bash_profile
RUN echo 'eval "$(pyenv init -)"' >> ~/.bash_profile

ENV HOME  /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install ${PYTHON_VERSION}
RUN pyenv global ${PYTHON_VERSION}
RUN pyenv rehash

RUN pip install --upgrade pip
RUN pip install PyYaml Markdown pika==0.10.0 aiohttp==2.0.5 pycryptodomex==3.4.5 aiopg==0.13.0 colorama==0.3.7 aiohttp-jinja2==0.13.0

##################################
# For SFTP
##################################
RUN mkdir -p /var/run/sshd
RUN groupadd --system sftp_users
COPY sshd_config /etc/ssh/sshd_config
COPY useradd_defaults /etc/default/useradd

RUN mkdir -p /etc/skel/.ssh && \
    chmod 700 /etc/skel/.ssh && \
    touch /etc/skel/.ssh/authorized_keys && \
    chmod 600 /etc/skel/.ssh/authorized_keys

EXPOSE 22

ENTRYPOINT ["/usr/sbin/sshd","-D", "-e"]
