FROM nbisweden/ega-os

#################################################
##
## Install LocalEGA and LocalEGA-cryptor
##
#################################################

RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml

ARG checkout=dev

RUN pip3.6 install -r https://raw.githubusercontent.com/NBISweden/LocalEGA-cryptor/master/requirements.txt
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA-cryptor.git

RUN pip3.6 install -r https://raw.githubusercontent.com/NBISweden/LocalEGA/${checkout}/requirements.txt
RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}
