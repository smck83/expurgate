![expurgate - simplify, hide and exceed SPF lookup limits](https://github.com/smck83/expurgate/blob/main/expurgate.png?raw=true)

A self-hosted,dockerized SPF solution leveraging rbldnsd as the DNS server to simplify, hide and exceed SPF lookup limits.

 # definition
    expurgate
    /ˈɛkspəːɡeɪt/
    verb
    remove matter thought to be objectionable or unsuitable from (a text or account).

SPF(Sender Policy Framework) records are DNS TXT records published by a domain owner so that e-mail that is sent from their domains can be checked by the receiving MTA as to whether the domain owner authorizes it.

NOTE: SPF does not prevent spoofing as it specifically relates to the domain name in the 'ENVELOPE FROM:' address which the recipient of the e-mail may never see. However a newer protocol called DMARC relies heavily on the SPF protocol to prevent spoofing.

# The problem
SPF records are publicly visible, prone to misconfiguration and limited to include 10 hostnames which could be A records, MX records or other TXT records called INCCLUDES. This includes nested records. 

Like all DNS records, TXT records are also limited to 255 chars per line meaning you not only have to juggle the hostname lookups but the length of each TXT record.



With the focus over the past 5 years for organisations adopting DMARC that rely on SPF and DKIM to prevent domain spoofing, as well as the average Enterprises using 110 Cloud/SaaS applications of which many need to spoof your domain, there has never been more reason for an organisation to exceed the 10 host resolution lookup limit

# The solution
### Simplify

### Hide
Replace your old SPF record that might look something like this:

    "v=spf1 include:sendgrid.net include:_spf.google.com include:mailgun.org include:spf.protection.outlook.com include:_netblocks.mimecast.com -all"

with an SPF Macro, removing hostnames and IP addresses from opportunistic threat actors that could use this information against you:

    "v=spf1 include:%{ir}.%{d}._spf.<your-domain> -all"

### Exceed SPF Limits
Expurgate resolves hostnames to IP address every X seconds and creates an RBLSDND configuration file. With only 1 INCLUDE: in your SPF record you never need to worry about exceeding the 10 lookup limit or the 255 character limit per line.

# Test it out
### An SPF pass checking 195.130.217.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.217.130.195.mimecast.com._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

Suppose an e-mail was sent using the ENVELOPE FROM: domain mimecast.com from the IP address 195.130.217.1
The recieving e-mail server will respond to the macro in you domains SPF record and interpret the below:

    ${ir} - the sending servers IP address in reverse. So 195.130.217.1 will be 1.217.130.195
    ${d} - the sending servers domain name (in ENVELOPE FROM: field) is mimecast.com

    The request: 
    1.217.130.195.mimecast.com._spf.xpg8.tk
    The response from expurgate:
    1.217.130.195.mimecast.com._spf.xpg8.tk. 300 IN	TXT "v=spf1 ip4:195.130.217.1 -all"

### An SPF fail checking 127.0.0.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.0.0.127.mimecast.com._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

    ${ir} - the sending servers IP address in reverse. So 127.0.0.1 will be 1.0.0.127
    ${d} - the sending servers domain name (in ENVELOPE FROM: field) is mimecast.com

    The request: 
    1.0.0.127.mimecast.com._spf.xpg8.tk
    The response from expurgate:
    1.0.0.127.mimecast.com._spf.xpg8.tk. 300 IN	TXT "v=spf1 -all"

# Cloud hosted SPF solutions
There are a number of vendors that offer SPF management capability. Each with pro's and con's. Some services use terms like SPF flattening and SPF compression.
