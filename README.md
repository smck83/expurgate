![expurgate - simplify, hide and exceed SPF lookup limits](https://github.com/smck83/expurgate/blob/main/expurgate.png?raw=true)

A self-hosted,dockerized SPF solution leveraging rbldnsd as the DNS server to simplify, hide and exceed SPF lookup limits.

 # definition
    expurgate
    /ˈɛkspəːɡeɪt/
    verb
    remove matter thought to be objectionable or unsuitable from (a text or account).

SPF records are DNS TXT records published by a domain owner so that e-mail sent from their domains can be validated as to whether or not the sending IP address is authorized. SPF does not prevent spoofing as it specifically relates tot eh domain name in the 'ENVELOPE FROM:' address which the recipient of the e-mail may never see.

# The problem
SPF(Sender Policy Framework) records are publicly visible, prone to misconfiguration and limited to include 10 hostnames which could be A records, MX records or other TXT records called INCCLUDES. This includes nested records. 

Like all DNS records, TXT records are also limited to 255 chars per line meaning you not only have to juggle the hostname lookups but the length of each TXT record.



With the focus over the past 5 years for organisations adopting DMARC that rely on SPF and DKIM to prevent domain spoofing, as well as the average Enterprises using 110 Cloud/SaaS applications of which many need to spoof your domain, there has never been more reason for an organisation to exceed the 10 host resolution lookup limit

# The solution
### Simplify

### Hide
Replace your old SPF record that might look something like this

    "v=spf1 include:sendgrid.net include:_spf.google.com include:mailgun.org include:spf.protection.outlook.com include:_netblocks.mimecast.com -all"

with an SPF Macro, removing hostnames and IP addresses from opportunistic threat actors that could use this information against you.

    "v=spf1 include:%{ir}.%{d}._spf.<your-domain> ~all"

### Exceed SPF Limits
Expurgate resolves hostnames to IP address every X seconds and creates an RBLSDND configuration file. With only 1 INCLUDE: in your SPF record you never need to worry about exceeding the 10 lookup limit or the 255 character limit per line.

# Other Commercial/Cloud hosted SPF solutions
There are a number of vendors that offer similiar capability, each with pro's and con's. Some services use terms like SPF flattening and SPF compression which often only solves 1 of the issues above.
