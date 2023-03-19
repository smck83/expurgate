![expurgate - simplify, hide and exceed SPF lookup limits](https://github.com/smck83/expurgate/blob/main/expurgate.png?raw=true)

A dockerized multi-domain SPF hosting solution leveraging rbldnsd as the DNS server to simplify, hide and exceed SPF lookup limits. The resolver script runs periodically to generate SPF Macro friendly configuration files for rbldnsd. 

My testing has proven performance with over 570 domains in `MY_DOMAINS`, running for 38 days; average resolution and file generation times are ~3 minutes versus < 1 minute when running resolver with pypy instead of python.

![image](https://github.com/smck83/expurgate/blob/main/python-vs-pypy.png)
 # What is Expurgate?
    expurgate
    /ˈɛkspəːɡeɪt/
    verb
    remove matter thought to be objectionable or unsuitable
    
Expurgate is a passion project that provides the capability to host your own SPF flattening (aka compression) management solution. There is no webUI and no database. With the exception of copying your existing SPF record to a subdomain, the entire configuration is completed using ENV variables parsed at runtime. This solution will resolve your SPF records hosted on an unused subdomain that will act as the source of truth for expurgate-resolver and is how you will make changes when you need to add or remove IP, subnets and hostnames. Expurgate-resolver will detect the changes on the subdomain and publish the new rbldnsd configuration for expurgate-rbldnsd. In the example below the subdomain `_sd6sdyfn.yourdomain.com` is used. The Expurgate SPF macro is then published on the root domain in place of the old record. A script running on the spf-resolver container will loop through the records hosted on the subdomain (no issues if they exceed 10 lookups or are duplicates) and generate an rbldnsd configuration file of IP addressess and subnets that rbldnsd will use..

Expurgate supports both IPv4 and IPv6 addresses.

NOTE: SPF(Sender Policy Framework) records are DNS TXT records published by a domain owner at the root(@) of your domain so that e-mail sent from the domain owners, domains can be validated by the receiving MTA to check if the domain owner authorizes the transmission. SPF does not prevent spoofing as it specifically relates to the domain name in the `ENVELOPE FROM:` address and according to `RFC 7208` standard the EHLO domain. The recipient (end user) of the e-mail will most likley never see the `ENVELOPE FROM:` address or EHLO domain so it is possible to PASS SPF but still spoof the domain in the `HEADER FROM:` address that the recipient will see. A newer protocol called DMARC `RFC 7489` relies heavily on the SPF (and DKIM) protocol to prevent spoofing.

You can read more on SPF here:
https://en.wikipedia.org/wiki/Sender_Policy_Framework#Principles_of_operation

# The problem
SPF records are publicly visible, prone to misconfiguration and limited to include 10 host DNS resolutions which could be A records, MX records or other TXT records called INCLUDE's. While you may only `INCLUDE` one other domain e.g. _spf.google.com this may very well link to 2 or 3 other hostnames which all count toward the RFC limit of 10. Further risk is that 3rd party providers in your SPF record may add a new host without communicating the specifics and while you have been keeping on top of your record, this could unknowingly push you over the limit.

Like most DNS records; TXT records are limited to 255 chars per line meaning if you attempt to juggle and manage SPF yourself, you not only have to count hostname lookups but the length of each TXT record.


With DMARC being listed in Gartner's top project list in 2021, more and more organasations are protecting their brand by preeventing e-mail domain spoofing that relies on SPF and DKIM. So, the requirement to exceed the SPF host lookup limit of 10 for a mid to large+ size organisation has never been greater. Expurgate makes the whole process easy, and means you don't have to juggle SPF on 10's or 100's of subdomains, deal with 253 line limits in TXT records or worry about the 10 SPF host resolution lookup limit.

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

`DISCLAIMER: Security through obscurity (or security by obscurity) is the reliance in security engineering on design or implementation secrecy as the main method of providing security to a system or component. While hiding SPF records may be beneficial, anyone on the internet can still check an IP against the record and whether it receives a PASS or FAIL. Technically brute force methods could be used against an SPF macro record; or targetted checks, e.g. lookup sengrid, microsoft, mailgun IP addresses to determine if a domain uses one of these vendors (or any others) - BGP prefix data could also be used to determine which IP within an enterprises subnets can e-mail on their behalf.`

### Exceed SPF Limits
Expurgate resolves hostnames to IP address and subnets every `DELAY=` seconds and generates an RBLSDND configuration file. With only 1 INCLUDE: in your new SPF record you never need to worry about exceeding the 10 lookup limit or the 255 character limit per line.

# How does it work?

![image](https://github.com/smck83/expurgate/blob/main/expurgate-diagram.png)

There are two seperate services running, with a third service being optional:
 1. The expurgate-resolver container is responsible for dynamically generating the rbldsnd config files
 2. The expurgate-rblsdnsd container is the DNS server listening on UDP/53
 3. \(OPTIONAL\) Use [dnsdist](https://dnsdist.org/) as a load balancer in front of rbldnsd to handle DDoS and support both UDP/53 + TCP/53

To keep the solution lightweight, no database or frontend UI is used, although these could be added to future version. Source records are stored in another obfuscated or hidden TXT record using a subdomain. This also means when the expurgate-resolver script runs it will regenerate config files when changes are detected which rbldnsd will automatically pickup.

# How do I run it?

For Step 3 & 4 use CLI or [Docker-compose.yaml](https://github.com/smck83/expurgate/blob/main/docker-compose.yaml)

### Step 1 - Create A + NS records
1)Create an A record e.g. spf-ns.yourdomain.com and point it to the public IP that will be hosting your expurgate-rbldnsd container on UDP/53 - you may wish to use [dnsdist](https://dnsdist.org/) in front of RBLDNSD to serve both TCP and UDP but also deal with DDoS.

    spf-ns.yourdomain.com. IN A 192.0.2.1
   
2)Then point your NS records of _spf.yourdomain.com to the A record, this will be what you set for `ZONE=` for expurgate-rbldnsd e.g.

    _spf.yourdomain.com. IN NS spf-ns.yourdomain.com

### Step 2 - Setup your source SPF record
Copy your current domains SPF record to an unused subdomain which will be set in `SOURCE_PREFIX=` e.g. _sd6sdyfn

    _sd6sdyfn.yourdomain.com.  IN  TXT "v=spf1 include:sendgrid.net include:mailgun.org -all"

### Step 3 - Run the expurgate-resolver first, so your RBLDNSD config is ready for the next step
    docker run -t -v /xpg8/rbldnsd-configs:/spf-resolver/output -e DELAY=300 -e MY_DOMAINS='xpg8.tk' -e SOURCE_PREFIX="_sd6sdyfn" --dns 1.1.1.1 --dns 8.8.8.8 smck83/expurgate-resolver

### Step 4 - Run expurgate-rbldnsd
      docker run -t -p 53:53/udp -v /xpg8/rbldnsd-configs:/var/lib/rbldnsd/:ro -e OPTIONS='-e -t 5m -l -' -e TYPE=combined -e ZONE=_spf.yourdomain.com smck83/expurgate-rbldnsd
### Step 5 - Replace your old SPF record with a macro pointing to expurgate-rbldsnd
    "v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all"
## Environment Variables
| Container  | Variable | Description | Required? |
| ------------- | ------------- | ------------- | ------------- |
| expurgate-resolver  | DELAY= | This is the delay in seconds between running the script to generate new RBLDNSD config files for RBLDNSD to pickup. `DEFAULT: 300` | N |
| expurgate-resolver  | MY_DOMAINS= | A list of domains seperated by a space that you want config files to be generated for. Example: `yourdomain.com microsoft.com github.com` | Y^ |
| expurgate-resolver  | SOURCE_PREFIX= | This is where you will publish your 'hidden' SPF record; the source of truth e.g. you might host it at _sd3fdsfd.yourdomain.com( so will be SOURCE_PREFIX=_sd3fdsfd) Default: `_xpg8` | N |
| expurgate-resolver  | SOURCE_PREFIX_OFF= | Only change for testing DEFAULT: `False` | N |
| expurgate-resolver  | UPTIMEKUMA_PUSH_URL= | Monitor expurgate-resolver health (uptime and time per loop) with an [Uptime Kuma](https://github.com/louislam/uptime-kuma) 'push' monitor. URL should end in ping= Example: `https://status.yourdomain.com/api/push/D0A90al0HA?status=up&msg=OK&ping=` | N |
| expurgate-resolver  | RUNNING_CONFIG_ON= | When set to: `1`, resolver will generate a single conf file called `running-config` for all domains in `MY_DOMAINS`, instead of one config file per domain. The main benefit is expurgate-rbldnsd doesnt need to be restarted to learn about new files and deleted domains.  | N |
| expurgate-rbldnsd  | OPTIONS= | These are rbldnsd run [options - more here](https://linux.die.net/man/8/rbldnsd) Recommend: `-e -t 5m -l -` <br/> `-e` = Allow non-network addresses to be used in CIDR ranges.<br/> `-t 5m` = Set TTL <br/>`l -` = Set Logfile to standard output | Y |
| expurgate-rbldnsd  | TYPE= | These are rbldnsd zone types [options - more here](https://linux.die.net/man/8/rbldnsd) Recommend: `combined`  | Y |
| expurgate-rbldnsd  | ZONE= | The last part of your SPF record (where rbldnsd is hosted), from step 1(2) EXAMPLE: `_spf.yourdomain.com`  | Y |

^ If left blank `SOURCE_PREFIX_OFF` will be set to true and container will run in demo mode using microsoft.com, mimecast.com and google.com

NOTE: Because one container is generating config files for the other container, it is IMPORTANT that both containers have their respective volumes mapped to the same path e.g. /xpg8/rbldnsd-config

# Sample Requests & Responses
## An SPF pass checking 66.249.80.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.80.249.66.ehlo.email._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

Suppose an e-mail was sent using the ENVELOPE FROM: domain ehlo.email from the IPv4 address `66.249.80.1`
The recieving e-mail server will respond to the macro in your domains SPF record and interpret the below:

${ir} - the sending servers IP address in reverse. So `66.249.80.1` will be `1.80.249.66`

${d} - the sending servers domain name (in `ENVELOPE FROM:` field) is `ehlo.email`

    The request: 
    
    1.80.249.66.ehlo.email_spf.xpg8.tk
    
    The response from expurgate-rbldnsd:
    
    1.80.249.66.ehlo.email._spf.xpg8.tk. 300 IN	TXT "v=spf1 ip4:66.249.80.1 -all"


NOTE(above): The response only includes the IP checked, and not every other vendor or provider in your `{SOURCE_PREFIX}.yourdomain.com` DNS TXT record.

## An SPF pass checking 2607:f8b0:4000:0000:0000:0000:0000:0001 - [Test here](https://www.digwebinterface.com/?hostnames=1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2.ehlo.email._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

Suppose an e-mail was sent using the ENVELOPE FROM: domain ehlo.email from the IPv6 address `2607:f8b0:4000:0000:0000:0000:0000:0001`
The recieving e-mail server will respond to the macro in your domains SPF record and interpret the below:

${ir} - the sending servers IP address in reverse. So `2607:f8b0:4000:0000:0000:0000:0000:0001` will be reversed in dotted notation `1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2`

${d} - the sending servers domain name (in ENVELOPE FROM: field) is `ehlo.email`

    The request: 
    
    1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2.ehlo.email._spf.xpg8.tk
    
    The response from expurgate-rbldnsd:
    
    1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2.ehlo.email._spf.xpg8.tk. 300 IN	TXT "v=spf1 ip6:2607:f8b0:4000::1 ~all"

## An SPF fail checking 127.0.0.1 - [Test here](https://www.digwebinterface.com/?hostnames=1.0.0.127.ehlo.email._spf.xpg8.tk&type=TXT&ns=resolver&useresolver=8.8.4.4&nameservers=)

${ir} - the sending servers IP address in reverse. So `127.0.0.1` will be `1.0.0.127`

${d} - the sending servers domain name (in ENVELOPE FROM: field) is `ehlo.email`

    The request: 
    
    1.0.0.127.ehlo.email._spf.xpg8.tk
    
    The response from expurgate-rbldnsd:
    
    1.0.0.127.ehlo.email._spf.xpg8.tk. 300 IN	TXT "v=spf1 -all"



# Cloud hosted SPF solutions
There are a number of vendors that offer SPF management capability. However I could not find any self-hosted options. Common terms for these services are SPF flattening and SPF compression.

# Recent enhancements
- pypy : As of 19/March/23 using pypy to run resolver script. This increases performance of DNS record generation by 5-10 x's
- AAAA Support: References to hostnames via A\A: or MX\MX: now perform a AAAA lookup to handle ip6 addresses.
- Expurgate Solo : an updated version where both rbldnsd and resolver are in a single docker container using supervisord https://github.com/smck83/expurgate-solo/
- Dedupe : If record already exists in 'list', do not add it again
- Write2Disk on Change: Instead of regenerating config files every time the script runs, the rbldnsd config will only be written should a record change since last run. A python dictionary is used to track this, however if scale is required REDIS or something similiar could be used.
- RestDB: RestDB capability has been added to manage MY_DOMAINS from restDB instead of via ENV.
- Running Config : Running config means a single rbldnsd config file is generated for ALL domains which means the expurgate-rbldnsd container doesnt need to restart if domains are added or removed from MY_DOMAINS or in RestDB
- Cache added : Given many INCLUDE: tend to be the same per source, e.g. mailgun.org, sendgrid.net, \_spf.google.com etc. A python disctionary has been added called dnsCache. If the record has already been looked up by another domain the respoonse the second or third+ time will come from memory, saving a DNS request.

# Buy me a coffee
If this was useful, feel free to [Buy me a coffee](https://www.buymeacoffee.com/smc83)
