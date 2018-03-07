FROM python:3.6-alpine3.7
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apk add --update \
    && apk add --no-cache build-base linux-headers bash git \
    && rm -rf /var/cache/apk/*

ARG DEV_PACKAGES=

# RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
#     yum -y install git gcc make bzip2 python36u python36u-pip nc ${DEV_PACKAGES} && \
#     yum clean all && rm -rf /var/cache/yum
#
# RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

ARG checkout=feature/pgp
# RUN pip3.6 install --upgrade pip && \
#     pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

RUN pip install --upgrade pip && \
    pip install git+https://github.com/NBISweden/LocalEGA.git@feature/pgp
