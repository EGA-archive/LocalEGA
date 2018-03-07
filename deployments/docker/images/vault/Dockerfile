FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ARG PIP_EGA_PACKAGES=

RUN pip install PyYaml ${PIP_EGA_PACKAGES}

ENV MQ_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
# CMD swe1
