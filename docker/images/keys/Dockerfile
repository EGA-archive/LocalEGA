FROM nbisweden/ega-worker:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg

COPY gpg-agent.conf /root/.gnupg/gpg-agent.conf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
CMD 9010
