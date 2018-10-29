FROM egarchive/base
LABEL maintainer "EGA System Developers"

#################################################
##
## Install LocalEGA stuff
##
#################################################

RUN groupadd -r lega && \
    useradd -M -r -g lega lega

RUN git clone https://github.com/EGA-archive/LocalEGA.git /root/LocalEGA

ARG checkout=master

RUN cd /root/LocalEGA && git checkout ${checkout}

# Requirements include crypt4gh (from https://github.com/EGA-archive/crypt4gh.git)
RUN pip3.6 install -r /root/LocalEGA/requirements.txt && \
    pip3.6 install /root/LocalEGA && \
    rm -rf /root/LocalEGA
