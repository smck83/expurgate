FROM python
LABEL maintainer="s@mck.la"
RUN apt-get update && apt-get install -y \
&& mkdir -p /spf-resolver/output \
&& pip install dnspython 
WORKDIR /spf-resolver
COPY . /spf-resolver

CMD ["python","./resolver.py"]
