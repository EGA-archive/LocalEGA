FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

ARG checkout=dev

RUN git clone https://github.com/NBISweden/LocalEGA /root/ega && \
    cd /root/ega && \
    git checkout ${checkout} && \
    pip3.6 install ./src
#    cd src && \
#    python3.6 setup.py install

ENTRYPOINT ["ega-frontend"]
