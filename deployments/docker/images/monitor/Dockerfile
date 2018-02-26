FROM python:3.6-alpine

RUN apk add --update \
    && apk add --no-cache build-base \
    && apk add --no-cache linux-headers \
    && apk add --no-cache bash \
    && apk add --no-cache py-setuptools \
&& rm -rf /var/cache/apk/*

RUN mkdir -p /app
RUN pip install asyncio aiohttp
COPY server.py /app
RUN chmod 755 /app/server.py

EXPOSE 5039

ENTRYPOINT ["python","/app/server.py"]
