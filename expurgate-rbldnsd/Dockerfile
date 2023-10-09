FROM debian:stable
LABEL maintainer="s@mck.la"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    rbldnsd ntp dnsutils\
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY running-config /var/lib/rbldnsd/running-config
VOLUME ["/var/lib/rbldnsd"]
WORKDIR /var/lib/rbldnsd

ENTRYPOINT /usr/sbin/rbldnsd -b 0.0.0.0 -n ${OPTIONS} ${ZONE}:${TYPE}:$(ls /var/lib/rbldnsd/| grep - | tr -s '\n' ',' | rev | cut -c 2- | rev)

EXPOSE 53/udp
