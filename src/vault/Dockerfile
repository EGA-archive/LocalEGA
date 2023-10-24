##########################
## Build env
##########################

FROM postgres:15 AS BUILD

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update; \
#    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends \
	    ca-certificates pkg-config git gcc make automake autoconf libtool \
            bzip2 zlib1g-dev libssl-dev libedit-dev libpq-dev postgresql-server-dev-15 \
            cmake

######### libsodium
COPY libsodium /var/src/libsodium

WORKDIR /var/src/libsodium
RUN ./configure
RUN make
RUN make check
RUN make install

######### Crypt4GH header pgxs
COPY pg_crypt4gh /var/src/pg_crypt4gh

WORKDIR /var/src/pg_crypt4gh
RUN make
RUN make install

############ For debug
RUN echo "alias ll='ls -al'" >> ~/.bashrc
RUN ldconfig -v

USER postgres
EXPOSE 5432
ENTRYPOINT ["postgres"]
CMD []


##########################
## Final image
##########################

FROM postgres:15

LABEL maintainer "CRG System Developers"

COPY --from=BUILD /usr/lib/postgresql/15                  /usr/lib/postgresql/15
COPY --from=BUILD /usr/share/postgresql/15                /usr/share/postgresql/15

# Dependencies
COPY --from=BUILD /usr/local/lib/libsodium*        /usr/local/lib/
COPY --from=BUILD /usr/local/lib/pkgconfig         /usr/local/lib/pkgconfig

RUN ldconfig -v

# We do not want to start the docker-entrypoint.sh script
USER postgres
EXPOSE 5432
ENTRYPOINT ["postgres"]
