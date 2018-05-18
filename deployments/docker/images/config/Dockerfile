FROM nbisweden/ega-base
LABEL maintainer "NBIS System Developers"

RUN yum -y install java-1.8.0-openjdk-devel && \
    yum clean all && rm -rf /var/cache/yum

WORKDIR /ega

RUN curl https://start.spring.io/starter.tgz \
-d type=maven-project \
-d language=java \
-d bootVersion=2.0.2.RELEASE \
-d baseDir=server \
-d groupId=se.nbis.lega \
-d artifactId=config \
-d name=config \
-d description="Local EGA Config Server" \
-d packageName=se.nbis.lega.config \
-d packaging=jar \
-d javaVersion=1.8 \
-d style=cloud-config-server | tar -xzvf -

WORKDIR /ega/server

RUN ./mvnw package

COPY bootstrap /ega/bootstrap
COPY extras/db.sql /tmp/db.sql
COPY extras/generate_pgp_key.py /tmp/generate_pgp_key.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN git config --global user.email "test@example.com"
RUN git config --global user.name "NBIS System Developers"

RUN echo $'server.port=8888 \n\
spring.applicaiton.name=config\n\
spring.profiles.active=fin\n\
spring.cloud.config.server.git.uri=file://ega/config\n'\
>> src/main/resources/application.properties

RUN sed -i '5iimport org.springframework.cloud.config.server.EnableConfigServer;' src/main/java/se/nbis/lega/config/ConfigApplication.java
RUN sed -i '7i@EnableConfigServer' src/main/java/se/nbis/lega/config/ConfigApplication.java

RUN chmod 755 /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
