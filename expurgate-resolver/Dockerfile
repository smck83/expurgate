FROM python:3-slim
#FROM pypy:3.9
LABEL maintainer="expurgate@mck.la"
RUN pip install dnspython requests jsonpath-ng \
&& mkdir -p /spf-resolver/output
WORKDIR /spf-resolver
COPY resolver.py /spf-resolver/resolver.py


CMD ["python3","./resolver.py"]
