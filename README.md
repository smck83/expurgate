# expurgate
A self-hosted,dockerized SPF solution built on rbldnsd to simplify, hide and exceed SPF lookup limits.

 # definition
   expurgate
   /ˈɛkspəːɡeɪt/
   verb
   remove matter thought to be objectionable or unsuitable from (a text or account).

# The problem
SPF records are DNS TXT records published by a domain owner so that receiving e-mail servers can validate whether or not the IP address is authorized to send an e-mail from the domain name in the  'ENVELOPE FROM:' address.

With the recent focus for organisations adopting DMARC that rely on SPF and DKIM to prevent domain spoofing, and on average Enterprises having 110 Cloud/SaaS applications of which many need to spoof your domain

SPF records are publicly visible, prone to misconfiguration due to 

# Other Commercial/Cloud hosted SPF solutions
 - Mimecast : SPF Delegation
 - AutoSPF : 
 - Proofpoint : SPF Hosting
 - Valimail
