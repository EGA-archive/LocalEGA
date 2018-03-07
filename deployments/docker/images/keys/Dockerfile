FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

ARG PIP_EGA_PACKAGES=
RUN pip install PyYaml ${PIP_EGA_PACKAGES}

ENTRYPOINT ["ega-keyserver","--keys","/etc/ega/keys.ini"]
