FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

ARG checkout=dev
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}  

ENTRYPOINT ["ega-frontend"]
