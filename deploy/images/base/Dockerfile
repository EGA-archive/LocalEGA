FROM egarchive/os
LABEL maintainer "EGA System Developers"

#################################################
##
## Install LocalEGA stuff
##
#################################################

# ARG cryptor_checkout=master
# RUN git clone https://github.com/EGA-archive/crypt4gh.git /root/crypt4gh && \
#     cd /root/crypt4gh && git checkout ${cryptor_checkout} && cd .. && \
#     pip3.6 install -r /root/crypt4gh/requirements.txt && \
#     rm -rf /root/crypt4gh

ARG checkout=master
RUN git clone https://github.com/EGA-archive/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout}

RUN pip3.6 install -r /root/LocalEGA/requirements.txt && \
    pip3.6 install /root/LocalEGA && \
    rm -rf /root/LocalEGA
