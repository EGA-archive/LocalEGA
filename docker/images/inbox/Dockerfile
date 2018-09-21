FROM nbisweden/ega-base as localega
LABEL maintainer "NBIS System Developers"

FROM nbisweden/ega-openssh

WORKDIR /
COPY --from=localega /usr/lib/python3.6 /usr/lib/python3.6
COPY --from=localega /usr/lib64/python3.6 /usr/lib64/python3.6
COPY --from=localega /usr/bin /usr/bin

EXPOSE 9000
VOLUME /ega/inbox

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
