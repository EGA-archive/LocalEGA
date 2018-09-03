FROM nbisweden/ega-base
LABEL maintainer "NBIS System Developers"

#################################################
##
## Install LocalEGA stuff
##
#################################################

ARG checkout=dev

RUN pip3.6 install -r https://raw.githubusercontent.com/NBISweden/LocalEGA/${checkout}/requirements.txt
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

RUN pip3.6 install -r https://raw.githubusercontent.com/NBISweden/LocalEGA-cryptor/master/requirements.txt
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA-cryptor.git
