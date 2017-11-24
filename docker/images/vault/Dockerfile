FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ARG checkout=dev

RUN git clone https://github.com/NBISweden/LocalEGA /root/ega && \
    cd /root/ega && \
    git checkout ${checkout} && \
    pip3.6 install ./src
#    cd src && \
#    python3.6 setup.py install

ENV MQ_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
# CMD swe1
