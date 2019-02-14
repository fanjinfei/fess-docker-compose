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
RUN sed -i '10 a <setproxy proxyhost="142.206.2.25" proxyport="80" proxyuser="fanjinf" proxypassword="Xinyun99" />' /usr/share/fess/bin/plugin.xml
RUN ant -f /usr/share/fess/bin/plugin.xml -Dtarget.dir=/tmp \
    -Dplugins.dir=/usr/share/elasticsearch/plugins install.plugins && \
    rm -rf /tmp/elasticsearch-*
RUN mkdir /opt/fess && \
    chown -R fess.fess /opt/fess && \
    sed -i -e 's#FESS_CLASSPATH="$FESS_CONF_PATH:$FESS_CLASSPATH"#FESS_CLASSPATH="$FESS_OVERRIDE_CONF_PATH:$FESS_CONF_PATH:$FESS_CLASSPATH"#g' /usr/share/fess/bin/fess
RUN echo "export FESS_APP_TYPE=$FESS_APP_TYPE" >>  /usr/share/fess/bin/fess.in.sh
RUN echo "export FESS_OVERRIDE_CONF_PATH=/opt/fess" >>  /usr/share/fess/bin/fess.in.sh
#RUN sed -i 's/8080/80/g' /usr/share/fess/bin/fess.in.sh
#RUN sed -i 's/FESS_USER=fess/FESS_USER=root/g' /etc/init.d/fess
#RUN sed -i 's/FESS_GROUP=fess/FESS_GROUP=root/g' /etc/init.d/fess

#RUN usermod -a -G root fess
#RUN usermod -a -G root elasticsearch

COPY elasticsearch/config /etc/elasticsearch

RUN curl https://bootstrap.pypa.io/get-pip.py | python && \
    pip install flask unicodecsv requests python-dateutil PyYAML gunicorn gevent flask_paginate flask_babel flask_compress

WORKDIR /usr/share/fess
EXPOSE 8090 8080 9200 9300

USER root
COPY run.sh /usr/share/fess/run.sh
RUN chmod +x /usr/share/fess/run.sh

RUN mkdir -p /usr/share/fess/config/backup
RUN mkdir -p /usr/share/fess/config/bin
COPY conf/fess_config.properties /etc/fess/fess_config.properties
COPY conf/admin_searchlist_edit.jsp /usr/share/fess/app/WEB-INF/view/admin/searchlist/admin_searchlist_edit.jsp
COPY conf/doc.json /usr/share/fess/app/WEB-INF/classes/fess_indices/fess/doc.json
COPY data/backup /usr/share/fess/config/backup
COPY data/bin /usr/share/fess/config/bin
COPY crawl*.py /usr/share/fess/config/bin/
COPY radar.yaml /usr/share/fess/config/bin/

#RUN sysctl -w vm.max_map_count=262144
ENTRYPOINT /usr/share/fess/run.sh
