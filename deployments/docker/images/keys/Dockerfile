FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

ARG PIP_EGA_PACKAGES=
RUN pip3.6 install PyYaml ${PIP_EGA_PACKAGES}

ENTRYPOINT ["/bin/ega-keyserver","--keys","/etc/ega/keys.ini"]
