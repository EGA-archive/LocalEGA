FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

#ARG checkout=dev
#RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}  

RUN mkdir /root/ega
COPY lega /root/ega/lega
COPY setup.py /root/ega/setup.py
RUN pip3.6 install -e /root/ega

ENTRYPOINT ["ega-frontend"]
