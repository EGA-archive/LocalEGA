FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install vim-common zlib-devel bzip2-devel

# Copy the RPMS from git
RUN for f in libgpg-error-1.27 libgcrypt-1.8.1 libassuan-2.4.3 libksba-1.3.5 npth-1.5 ncurses-6.0 pinentry-1.0.0 gnupg-2.2.2; \
    do curl -OL https://github.com/NBISweden/LocalEGA/raw/dev/extras/rpmbuild/RPMS/x86_64/${f}-1.el7.centos.x86_64.rpm; \
       rpm -i ${f}-1.el7.centos.x86_64.rpm; \
       rm ${f}-1.el7.centos.x86_64.rpm; \
    done

RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

ARG checkout=dev
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

RUN mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg

COPY gpg-agent.conf /root/.gnupg/gpg-agent.conf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENV KEYSERVER_PORT=
ENTRYPOINT ["entrypoint.sh"]
