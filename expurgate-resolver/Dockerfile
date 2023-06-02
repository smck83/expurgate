FROM pypy:3
LABEL maintainer="expurgate@mck.la"
RUN pip install dnspython requests jsonpath-ng \
&& mkdir -p /spf-resolver/output
WORKDIR /spf-resolver
COPY resolver.py /spf-resolver

CMD ["pypy3","./resolver.py"]
