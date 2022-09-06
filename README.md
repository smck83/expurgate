# expurgate
A self-hosted,dockerized SPF solution leveraging rbldnsd as the DNS server to simplify, hide and exceed SPF lookup limits.

 # definition
    expurgate
    /ˈɛkspəːɡeɪt/
    verb
    remove matter thought to be objectionable or unsuitable from (a text or account).

# The problem
SPF(Sender Policy Framework) records are publicly visible, prone to misconfiguration and limited to include 10 hostnames which could be A records, MX records or other TXT records called INCCLUDES. This includes nested records. 

Like all DNS records, TXT records are also limited to 255 chars per line of a 

SPF records are DNS TXT records published by a domain owner so that e-mail sent from their domains can be validated as to whether or not the sending IP address is authorized. SPF does not prevent spoofing as it specifically relates tot eh domain name in the 'ENVELOPE FROM:' address which the recipient of the e-mail may never see.


With the focus over the past 5 years for organisations adopting DMARC that rely on SPF and DKIM to prevent domain spoofing, as well as the average Enterprises using 110 Cloud/SaaS applications of which many need to spoof your domain, there has never been more reason for an organisation to exceed the 10 host resolution lookup limit

# The solution
expurgate

# Other Commercial/Cloud hosted SPF solutions
 - Mimecast : SPF Delegation
 - AutoSPF
 - Proofpoint : SPF Hosting
 - Valimail
 - Agari
