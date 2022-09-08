
from time import sleep
import dns.resolver
import re
from datetime import datetime
import os

# set to 0 to loop infinitely
loop = 0
# set the depth to count resolutions
global depth
depth = 0

if 'SOURCE_PREFIX_OFF' in os.environ:
    source_prefix_off = os.environ['SOURCE_PREFIX_OFF']
else:
    source_prefix_off = False # set to True to be able to run against root domain
if 'SOURCE_PREFIX' in os.environ:
    source_prefix  = os.environ['SOURCE_PREFIX']
else:
    #if not specified, store your 'hidden' record at _xpg8.<yourdomain>
    source_prefix = ['_xpg8']
if 'MY_DOMAINS' in os.environ:
    domains = os.environ['MY_DOMAINS']
    mydomains = domains.split(' ')
else:
    #example list if MY_DOMAINS isnt provided
    source_prefix_off = True
    mydomains = ['google.com','mimecast.com','microsoft.com']
    print("MY_DOMAIN not set, running in demo mode using " + str(mydomains))
if 'DELAY' in os.environ and int(os.environ['DELAY']) > 29:
    delayBetweenRun = os.environ['DELAY']
else:
    delayBetweenRun = 300 #default to 5 minutes
print("Running delay of : " + str(delayBetweenRun))


def getSPF(domain):
    global depth
    try:
        #try:
        if depth == 0 and source_prefix_off == False:
           result = [dns_record.to_text() for dns_record in dns.resolver.resolve(source_prefix + "." + domain, "TXT").rrset]
        #except:
        elif depth <= 75:
            result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "TXT").rrset]
        else:
            print("THERE MAY BE A SPF LOOP, EXITING AFTER GOING 75 DEEP")
            result = "\"v=spf1 -all\""
    
    except:
        print("An exception occurred, check there is a DNS TXT record with SPF present at: " + source_prefix + "." + domain )
        result = "\"v=spf1 -all\""
    depth += 1

    #print("Depth:" + str(depth))
    for record in result:
        if re.match('^"v=spf1 ', record):
            # replace " " with nothing which is used where TXT records exceed 255 characters
            record = record.replace("\" \"","")
            ip4.append("# " + record)
            # remove " character from start and end
            spfvalue = record.replace("\"","")
            spfParts = spfvalue.split()
 
            for spfPart in spfParts:
                if re.match('redirect=', spfPart):
                    spfValue = spfPart.split('=')
                    getSPF(spfValue[1])
                elif re.match('include\:', spfPart) and "%{" not in spfPart:
                    spfValue = spfPart.split(':')
                    ip4.append("# " + spfPart)
                    # ip6.append("# " + spfPart)
                    getSPF(spfValue[1])
                    #print(spfValue[1])
                elif re.match('a\:', spfPart):
                    ip4.append("# " + spfPart)
                    spfValue = spfPart.split(':')
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(spfValue[1], "A").rrset]
                    depth += 1
                    result = (" # " + spfValue[0] + ":" + spfValue[1] + " \n").join(result)

                    ip4.append(result + " # " + spfPart)
                elif re.match('a', spfPart):
                    ip4.append("# " + spfPart)
                    #spfValue = spfPart.split('a:')
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "A").rrset]
                    depth += 1
                    result = '\n'.join(result)
                    ip4.append(result + " # a")
                elif re.match('mx\:', spfPart):
                    ip4.append("# " + spfPart)
                    spfValue = spfPart.split(':')
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(spfValue[1], "MX").rrset]
                    depth += 1
                    myarray = []
                    for mxrecord in result:
                        mxValue = mxrecord.split(' ')
                        myarray.append(mxValue[1])
                    #print(myarray)
                    for hostname in myarray:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(hostname, "A").rrset]
                        result = '\n'.join(result)
                        #print(hostname + ":" + result)
                        ip4.append(result)
                elif re.match('mx', spfPart):
                    ip4.append("# " + spfPart)
                    try:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "MX").rrset]
                    except:
                        print("Error performing MX lookup")
                    depth += 1
                    myarray = []
                    for mxrecord in result:
                        mxValue = mxrecord.split(' ')
                        myarray.append(mxValue[1])
                    #print(myarray)
                    for hostname in myarray:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(hostname, "A").rrset]
                        depth += 1
                        result = '\n'.join(result)
                        ip4.append(result)
                elif re.match('ip4\:', spfPart):
                    spfValue = spfPart.split('ip4:')
                    ip4.append(spfValue[1] + " # " + domain)
                elif re.match('ip6\:', spfPart):
                    spfValue = spfPart.split('ip6:')
                    ip6.append(spfValue[1] + " # " + domain)
                elif re.match('[\+\-\~]all', spfPart):
                    spfAction.append(spfPart)
                elif re.match('v\=spf1', spfPart):
                    spfValue = spfPart
                else:
                    print('No match:',spfPart)
                    otherValues.append(spfPart)

while loop == 0:
    print('Generating config for SPF records in ' + str(mydomains))
    for domain in mydomains:
        ip4 = []
        ip6 = []
        spfAction = ["~all"]
        otherValues = []
        depth = 0
        getSPF(domain)

    # remove duplicates
        print(len(ip4)) 
        ip4 = list(dict.fromkeys(ip4))
        ip4 = [x.strip(' ') for x in ip4]
        #ip4 = ip4.sort
        print(len(ip4),ip4)  
        # remove duplicates
        print(len(ip6)) 
        ip6 = list(dict.fromkeys(ip6))
        ip6 = [x.strip(' ') for x in ip6]
        #ip6 = ip6.sort
        print(len(ip6),ip6)  
        
    # CREATE ARRAYS FOR EACH PART OF THE RBLDNSD FILE
        datetimeNow = datetime.now(tz=None)
        ip4header = ["# Automatically generated rbldnsd config by Expurgate for:" + domain + " @ " + str(datetimeNow)]
        ip4header.append("# Depth:" + str(depth))
        ip4header.append("$DATASET ip4set:"+ domain +" " + domain + " @")
        ip4header.append(":3:v=spf1 ip4:$ " + spfAction[0])

        if len(otherValues) > 0:
            ip4block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
        else:
            ip4block = [":99:v=spf1 " + spfAction[0]]
        ip4block.append("0.0.0.0/1")
        ip4block.append("128.0.0.0/1")
        ip6header = ["$DATASET ip6trie:"+ domain +" " + domain + " @"]
        ip6header.append(":3:v=spf1 ip6:$ " + spfAction[0])
        if len(otherValues) > 0:
            ip6block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
        else:
            ip6block = [":99:v=spf1 " + spfAction[0]]
        ip6block.append("0:0:0:0:0:0:0:0/0")
        # Join all the pieces together, ready for file output
        myrbldnsdconfig = ip4header + ip4 + ip4block + ip6header + ip6 + ip6block

        # Write the RBLDNSD config file to disk
        with open(r'output/'+ domain.replace(".","-"), 'w') as fp:
            for item in myrbldnsdconfig:
                # write each item on a new line
                fp.write("%s\n" % item)
            print('Generating rbldnsd config for SPF records in ' + domain)
            print("Your domain " + domain + " required " + str(depth) + " lookups.")
    print("Waiting " + str(delayBetweenRun) + " seconds before running again... ")
    #print("Waiting...")
    sleep(int(delayBetweenRun)) # wait DELAY before running again.