FROM debian:stable
LABEL maintainer="s@mck.la"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    rbldnsd ntp dnsutils\
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN apt-get update && apt-get install -y software-properties-common wget xz-utils build-essential \
    libffi-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
RUN wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tar.xz
RUN tar -xf Python-3.11.1.tar.xz
RUN cd Python-3.11.1 && ./configure --enable-optimizations && make altinstall

LABEL maintainer="expurgate@mck.la"
RUN apt-get update && apt-get install -y python3-pip
RUN pip install dnspython requests jsonpath-ng --break-system-packages

RUN apt-get update && apt-get install -y supervisor

COPY running-config /var/lib/rbldnsd/running-config
COPY resolver.py /spf-resolver/resolver.py
RUN mkdir -p /spf-resolver && ln -sf /var/lib/rbldnsd /spf-resolver/output

ENV DELAY=300
ENV MY_DOMAINS="yourdomain.com yourdomain2.com yourdomain3.com"
ENV SOURCE_PREFIX=_sd6sdyfn
ENV RUNNING_CONFIG_ON=1
ENV OPTIONS="-e -t 5m -l -"
ENV TYPE=combined
ENV ZONE=_spf.yourdomain.com

RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENTRYPOINT ["/usr/bin/supervisord"]

EXPOSE 53/udp
