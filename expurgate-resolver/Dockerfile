FROM python:3-alpine
LABEL maintainer="expurgate@mck.la"
RUN apk -U upgrade \
&& pip install dnspython requests jsonpath-ng \
&& mkdir -p /spf-resolver/output
WORKDIR /spf-resolver
COPY . /spf-resolver

CMD ["python","./resolver.py"]
