FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ARG checkout=dev
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

ENV MQ_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
# CMD swe1
