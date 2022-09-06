![expurgate - simplify, hide and exceed SPF lookup limits](https://github.com/smck83/expurgate/blob/main/expurgate.png?raw=true)

A self-hosted,dockerized SPF solution leveraging rbldnsd as the DNS server to simplify, hide and exceed SPF lookup limits.

 # definition
    expurgate
    /ˈɛkspəːɡeɪt/
    verb
    remove matter thought to be objectionable or unsuitable

SPF(Sender Policy Framework) records are DNS TXT records published by a domain owner so that e-mail that is sent from their domains can be checked by the receiving MTA as to whether the domain owner authorizes it.

NOTE: SPF does not prevent spoofing as it specifically relates to the domain name in the 'ENVELOPE FROM:' address and according to the RFC standard the EHLO domain. The recipient of the e-mail will most likley never see these addresses so it is possible to PASS SPF but still spoof the HEADER FROM: address that the recipient will see. A newer protocol called DMARC relies heavily on the SPF protocol to prevent spoofing.

# The problem
SPF records are publicly visible, prone to misconfiguration and limited to include 10 hostnames which could be A records, MX records or other TXT records called INCLUDE's. While you may only INCLUDE: one other domain e.g. _spf.google.com this may very well link to 2 or 3 other hostnames which all count toward the RFC limit of 10.

Like all DNS records, TXT records are also limited to 255 chars per line meaning you not only have to juggle the hostname lookups but the length of each TXT record.


With the focus over the past 5 years for organisations adopting DMARC that rely on SPF and DKIM to prevent domain spoofing, as well as the average Enterprises using 110 Cloud/SaaS applications of which many need to spoof your domain, there has never been more reason for an organisation to exceed the 10 host resolution lookup limit

# The solution
### Simplify
Expurgate simplifies DNS management for SPF by using a single record with variables. This removes the chance of human error and isolates issues with loops and broken upstream SPF records.

### Hide
Copy your old SPF record to unused subdomain defined in `SOURCE_PREFIX=`. Your old SPF record might look something like this:

    "v=spf1 include:sendgrid.net include:_spf.google.com include:mailgun.org include:spf.protection.outlook.com include:_netblocks.mimecast.com -all"

By using an SPF Macro in place of your old SPF record, we remove hostnames and IP addresses from opportunistic threat actors prying eyes that could use this information against you (e.g. Phishing e-mails using sendgrid branding based on include:sendgrid.net being present:

https://emailstuff.org/spf/check/macro.xpg8.tk

    "v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all"

The old SPF record not only gives away the names of all the service providers you use that need to legitimately spoof your domain, but this sample record [exceeds the 10 lookup limit](https://emailstuff.org/spf/check/10plus.xpg8.tk).


### Exceed SPF Limits
Expurgate resolves hostnames to IP address and subnets every `DELAY=` seconds and generates an RBLSDND configuration file. With only 1 INCLUDE: in your new SPF record you never need to worry about exceeding the 10 lookup limit or the 255 character limit per line.

# How does it work?
There are two seperate services running, with a third service being optional:
 1. The expurgate-resolver container is responsible for dynamically generating the rbldsnd config files
 2. The expurgate-rblsdnsd container is the DNS server listening on UDP/53
 3. \(OPTIONAL\) Use [dnsdist](https://dnsdist.org/) as a load balancer in front of rbldnsd to handle DDoS and support both UDP/53 + TCP/53

To keep the solution lightweight, no database is used to track changes and source records are stored in another obfuscated or hidden TXT record. This also means when the expurgate-resolver script runs it will regenerate ALL config files which rbldnsd will automatically pickup.

# How do I run it?

## Docker-compose.yaml
You can simply use the docker-compose.yaml file [hosted here](https://github.com/smck83/expurgate/blob/main/docker-compose.yaml).

## Docker CLI
### Step 1 - Create A + NS records
1)Create an A record e.g. spf-ns.yourdomain.com and point it to the public IP that will be hosting your expurgate-rbldnsd container on UDP/53 - you may wish to use [dnsdist](https://dnsdist.org/) in front of RBLDNSD to serve both TCP and UDP but also deal with DDoS.

    spf-ns.yourdomain.com. IN A 192.0.2.1
   
2)Then point your NS records of _spf.yourdomain.com to the A record, this will be what you set for `ZONE=` for expurgate-rbldnsd e.g.

    _spf.yourdomain.com. IN NS spf-ns.yourdomain.com

### Step 2 - Setup your source SPF record
Copy your current domains SPF record to the subdomain which will be set in `SOURCE_PREFIX=` e.g. _sd6sdyfn

    _sd6sdyfn.yourdomain.com.  IN  TXT "v=spf1 include:sendgrid.net include:mailgun.org -all"

### Step 3 - Run the expurgate-resolver first, so your RBLDNSD config is ready for the next step
    docker run -t -v /xpg8/rbldnsd-configs:/spf-resolver/output -e DELAY=300 -e MY_DOMAINS='xpg8.tk' -e SOURCE_PREFIX="_sd6sdyfn" --dns 1.1.1.1 --dns 8.8.8.8 smck83/expurgate-resolver

### Step 4 - Run expurgate-rbldnsd
      docker run -t -p 53:53/udp -v /xpg8/rbldnsd-configs:/var/lib/rbldnsd/:ro -e OPTIONS='-e -t 5m -l -' -e TYPE=combined -e ZONE=_spf.yourdomain.com smck83/expurgate-rbldnsd
### Step 5 - Replace your old SPF record with a macro pointing to expurgate
    "v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all"
## Environment Variables
| Container  | Variable | Description |
| ------------- | ------------- | ------------- |
| expurgate-resolver  | DELAY= | This is the delay in seconds between running the script to generate new RBLDNSD config files for RBLDNSD to pickup.
| expurgate-resolver  | MY_DOMAINS= | A list of domains seperated by a space that you want config files to be generated for e.g. MY_DOMAINS='yourdomain.com microsoft.com github.com' |
 | expurgate-resolver  | SOURCE_PREFIX= | This is where you will publish your 'hidden' SPF record e.g. you might host it at _sd3fdsfd.yourdomain.com so will be SOURCE_PREFIX=_sd3fdsfd |
| expurgate-rbldnsd  | OPTIONS= | These are rbldnsd run [options - more here](https://linux.die.net/man/8/rbldnsd) Recommend: -e -t 5m -l - |
| expurgate-rbldnsd  | TYPE= | These are rbldnsd zone types [options - more here](https://linux.die.net/man/8/rbldnsd) Recommend: combined |
| expurgate-rbldnsd  | ZONE= | The last part of your SPF record (where rbldnsd is hosted), from step 1(2) e.g. "ZONE=_spf.yourdomain.com" |

NOTE: Because one container is generating config files for the other container, it is IMPORTANT that both containers have their respective volumes mapped to the same path e.g. /xpg8/rbldnsd-config

# Sample Requests & Reponses
## An SPF pass checking 195.130.217.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.217.130.195.mimecast.com._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

Suppose an e-mail was sent using the ENVELOPE FROM: domain mimecast.com from the IP address 195.130.217.1
The recieving e-mail server will respond to the macro in you domains SPF record and interpret the below:

    ${ir} - the sending servers IP address in reverse. So 195.130.217.1 will be 1.217.130.195
    ${d} - the sending servers domain name (in ENVELOPE FROM: field) is mimecast.com

    The request: 
    1.217.130.195.mimecast.com._spf.xpg8.tk
    The response from expurgate:
    1.217.130.195.mimecast.com._spf.xpg8.tk. 300 IN	TXT "v=spf1 ip4:195.130.217.1 -all"

NOTE(above): The response only includes the IP checked, and not every other vendor or provider in your `{SOURCE_PREFIX}.yourdomain.com' DNS TXT record.

## An SPF fail checking 127.0.0.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.0.0.127.mimecast.com._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

    ${ir} - the sending servers IP address in reverse. So 127.0.0.1 will be 1.0.0.127
    ${d} - the sending servers domain name (in ENVELOPE FROM: field) is mimecast.com

    The request: 
    1.0.0.127.mimecast.com._spf.xpg8.tk
    The response from expurgate:
    1.0.0.127.mimecast.com._spf.xpg8.tk. 300 IN	TXT "v=spf1 -all"



# Cloud hosted SPF solutions
There are a number of vendors that offer SPF management capability. However I could not find any self-hosted options. Common terms for these services are SPF flattening and SPF compression.
