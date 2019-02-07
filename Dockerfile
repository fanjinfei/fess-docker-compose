FROM openjdk:8-jre
LABEL maintainer "N2SM <support@n2sm.net>"

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

ENV ES_DOWNLOAD_URL https://artifacts.elastic.co/downloads/elasticsearch
ENV FESS_APP_TYPE docker

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
      imagemagick \
      procps \
      unoconv \
      ant \
      nodejs \
      && \
    npm install elasticdump -g && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ARG FESS_VERSION=12.4.3
ARG ELASTIC_VERSION=6.5.4

RUN groupadd -g 1000 elasticsearch && \
    groupadd -g 1001 fess && \
    useradd -u 1000 elasticsearch -g elasticsearch && \
    useradd -u 1001 fess -g fess

RUN set -x && \
    wget --progress=dot:mega ${ES_DOWNLOAD_URL}/elasticsearch-oss-${ELASTIC_VERSION}.deb \
      -O /tmp/elasticsearch-${ELASTIC_VERSION}.deb && \
    dpkg -i /tmp/elasticsearch-${ELASTIC_VERSION}.deb && \
    rm -rf /tmp/elasticsearch-${ELASTIC_VERSION}.deb

RUN set -x && \
    wget --progress=dot:mega https://github.com/codelibs/fess/releases/download/fess-${FESS_VERSION}/fess-${FESS_VERSION}.deb -O /tmp/fess-${FESS_VERSION}.deb && \
    dpkg -i /tmp/fess-${FESS_VERSION}.deb && \
    rm -rf /tmp/fess-${FESS_VERSION}.deb
#RUN export  ANT_OPTS="-Dhttp.proxyHost=12.26.2.2 -Dhttp.proxyPort=80 -Dhttp.proxyUser=x -Dhttp.proxyPassword=y" 
#RUN sed -i '10 a <setproxy proxyhost="12.26.2.2" proxyport="80" proxyuser="x" proxypassword="y" />' /usr/share/fess/bin/plugin.xml
RUN export  ANT_OPTS="-Dhttp.proxyHost=12.26.2.2 -Dhttp.proxyPort=80 -Dhttp.proxyUser=x -Dhttp.proxyPassword=y" && \
    ant -f /usr/share/fess/bin/plugin.xml -Dtarget.dir=/tmp \
    -Dplugins.dir=/usr/share/elasticsearch/plugins install.plugins && \
    rm -rf /tmp/elasticsearch-*
RUN mkdir /opt/fess && \
    chown -R fess.fess /opt/fess && \
    sed -i -e 's#FESS_CLASSPATH="$FESS_CONF_PATH:$FESS_CLASSPATH"#FESS_CLASSPATH="$FESS_OVERRIDE_CONF_PATH:$FESS_CONF_PATH:$FESS_CLASSPATH"#g' /usr/share/fess/bin/fess
RUN echo "export FESS_APP_TYPE=$FESS_APP_TYPE" >>  /usr/share/fess/bin/fess.in.sh
RUN echo "export FESS_OVERRIDE_CONF_PATH=/opt/fess" >>  /usr/share/fess/bin/fess.in.sh
RUN sed -i 's/8080/80/g' /usr/share/fess/bin/fess.in.sh
RUN sed -i 's/FESS_USER=fess/FESS_USER=root/g' /etc/init.d/fess
RUN sed -i 's/FESS_GROUP=fess/FESS_GROUP=root/g' /etc/init.d/fess

RUN usermod -a -G root fess

COPY elasticsearch/config /etc/elasticsearch

WORKDIR /usr/share/fess
EXPOSE 80 9200 9300

USER root
COPY run.sh /usr/share/fess/run.sh
RUN chmod +x /usr/share/fess/run.sh
#RUN sysctl -w vm.max_map_count=262144
ENTRYPOINT /usr/share/fess/run.sh
