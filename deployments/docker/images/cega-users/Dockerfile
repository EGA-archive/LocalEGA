FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

##################################
RUN mkdir /cega
VOLUME /cega/users
EXPOSE 80

RUN pip3.6 install aiohttp aiohttp-jinja2

COPY users.html /cega/users.html

COPY server.py /cega/server.py
RUN chmod 755 /cega/server.py

CMD ["/cega/server.py"]
