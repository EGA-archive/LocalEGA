FROM gpg:2.1
LABEL maintainer "Frédéric Haziza, NBIS"

##############################################################
ARG PYTHON_VERSION=3.6.1

RUN git clone git://github.com/yyuu/pyenv.git ~/.pyenv && \
    echo 'export PYENV_ROOT=$HOME/.pyenv' >> ~/.bash_profile && \
    echo 'export PATH=$PYENV_ROOT/bin:$PATH' >> ~/.bash_profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile

ENV HOME  /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash

RUN pip install --upgrade pip && \
    pip install PyYaml Markdown pika==0.10.0 aiohttp==2.0.5 pycryptodomex==3.4.5 aiopg==0.13.0 colorama==0.3.7 aiohttp-jinja2==0.13.0

##############################################################
COPY gpg.conf       /root/.gnupg/gpg.conf
COPY gpg-agent.conf /root/.gnupg/gpg-agent.conf
COPY ssh_config     /root/.ssh/config
COPY sshd_config    /etc/ssh/sshd_config
