
from time import sleep
import dns.resolver
import re
from datetime import datetime
import os
import shutil

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
           sourcerecord = source_prefix + "." + domain
           result = [dns_record.to_text() for dns_record in dns.resolver.resolve(sourcerecord, "TXT").rrset]
        #except:
        elif depth <= 75:
            result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "TXT").rrset]        
        else:
            msg = "THERE MAY BE A SPF LOOP, EXITING AFTER GOING 75 DEEP"
            print(msg)
            result = "\"v=spf1 -all\""
            depth += 1  
            header.append("# " + ("^" * depth) + " " + msg) 
    
    except:
        print("An exception occurred, check there is a DNS TXT record with SPF present at: " + str(source_prefix) + "." + str(domain) )
        result = "\"v=spf1 -all\""

    for record in result:
        if re.match('^"v=spf1 ', record, re.IGNORECASE):
            # replace " " with nothing which is used where TXT records exceed 255 characters
            record = record.replace("\" \"","")
            # remove " character from start and end
            spfvalue = record.replace("\"","")
            spfParts = spfvalue.split()
            header.append("# " + ("^" * depth) + " " + domain)           
            header.append("# " + ("^" * depth) + " " + spfvalue)

            for spfPart in spfParts:
                if re.match('redirect=', spfPart, re.IGNORECASE):
                    spfValue = spfPart.split('=')
                    depth += 1         
                    getSPF(spfValue[1])
                elif re.match('include\:', spfPart, re.IGNORECASE) and "%{" not in spfPart:
                    spfValue = spfPart.split(':')
                    depth += 1
                    getSPF(spfValue[1])
                elif re.match('a\:', spfPart, re.IGNORECASE):
                    spfValue = spfPart.split(':')
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(spfValue[1], "A").rrset]
                    depth += 1
                    header.append("# " + ("^" * depth) + " " + spfPart)
                    result = [x + ' # a:' + spfValue[1] for x in result]
                    result = ('\n').join(result)
                    ip4.append(result + " # " + spfPart)
                elif re.match('a', spfPart, re.IGNORECASE):
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "A").rrset]
                    depth += 1
                    header.append("# " + ("^" * depth) + " " + spfPart + "(" + domain + ")")
                    result = (' # a(' + hostname + ')\n').join(result)
                    ip4.append(result + " # a")
                elif re.match('mx\:', spfPart, re.IGNORECASE):
                    spfValue = spfPart.split(':')
                    result = [dns_record.to_text() for dns_record in dns.resolver.resolve(spfValue[1], "MX").rrset]
                    depth += 1       
                    header.append("# " + ("^" * depth) + " " + spfPart)   
                    myarray = []
                    for mxrecord in result:
                        mxValue = mxrecord.split(' ')
                        myarray.append(mxValue[1])
                    for hostname in myarray:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(hostname, "A").rrset]
                        depth += 1
                        result = (' # ' + spfPart + '=>a:' + hostname + '\n').join(result)
                        ip4.append(result)
                        header.append("# " + ("^" * depth) + " " + spfPart + "=>a:" + hostname)

                elif re.match('mx', spfPart, re.IGNORECASE):
                    try:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, "MX").rrset]
                        depth += 1
                        header.append("# " + ("^" * depth) + " mx(" + domain + ")")
                    except:
                        print("Error performing MX lookup")
                    myarray = []
                    for mxrecord in result:
                        mxValue = mxrecord.split(' ')
                        myarray.append(mxValue[1])
                    for hostname in myarray:
                        result = [dns_record.to_text() for dns_record in dns.resolver.resolve(hostname, "A").rrset]
                        depth += 1
                        result = (' # mx(' + domain + ')=>a:' + hostname + '\n').join(result)
                        ip4.append(result)
                        header.append("# " + ("^" * depth) + " mx(" + domain + ")=>a:" + hostname)

                elif re.match('ip4\:', spfPart, re.IGNORECASE):
                    spfValue = spfPart.split('ip4:')
                    ip4.append(spfValue[1] + " # " + domain)
                elif re.match('ip6\:', spfPart, re.IGNORECASE):
                    spfValue = spfPart.split('ip6:')
                    ip6.append(spfValue[1] + " # " + domain)
                elif re.match('[\+\-\~\?]all', spfPart, re.IGNORECASE):
                    spfAction.append(spfPart)
                elif re.match('v\=spf1', spfPart, re.IGNORECASE):
                    spfValue = spfPart
                else:
                    print('No match:',spfPart)
                    otherValues.append(spfPart)

while loop == 0:
    print('Generating config for SPF records in ' + str(mydomains))
    for domain in mydomains:
        datetimeNow = datetime.now(tz=None)
        header = ["# Automatically generated rbldnsd config by Expurgate for:" + domain + " @ " + str(datetimeNow)]
        ip4 = []
        ip4header = []
        ip6 = []
        ip6header = []
        spfAction = ["~all"]
        otherValues = []
        depth = 0
        getSPF(domain)

    # remove duplicates
        print("Items in IP4: array (before dedupe):" + str(len(ip4))) 
        ip4 = list(dict.fromkeys(ip4))
        ip4 = [x.strip(' ') for x in ip4]
        print("Items in IP4: array (after dedupe):" + str(len(ip4)))  
        print(ip4)
        # remove duplicates
        print("Items in IP6: array (before dedupe):" + str(len(ip6))) 
        ip6 = list(dict.fromkeys(ip6))
        ip6 = [x.strip(' ') for x in ip6]
        print("Items in IP6: array (after dedupe):" + str(len(ip6)))  
        print(ip6)
        
    # CREATE ARRAYS FOR EACH PART OF THE RBLDNSD FILE
        ip4header.append("# Depth:" + str(depth))
        ip4header.append("$DATASET ip4set:"+ domain +" " + domain + " @")
        ip4header.append(":3:v=spf1 ip4:$ " + spfAction[0])

        if len(otherValues) > 0:
            ip4block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
        else:
            ip4block = [":99:v=spf1 " + spfAction[0]]
        ip4block.append("0.0.0.0/1 # all other IPs")
        ip4block.append("128.0.0.0/1 # all other IPs")
        ip6header.append("$DATASET ip6trie:"+ domain +" " + domain + " @")
        ip6header.append(":3:v=spf1 ip6:$ " + spfAction[0])
        if len(otherValues) > 0:
            ip6block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
        else:
            ip6block = [":99:v=spf1 " + spfAction[0]]
        ip6block.append("0:0:0:0:0:0:0:0/0 # all other IPs")
        # Join all the pieces together, ready for file output
        myrbldnsdconfig = header + ip4header + ip4 + ip4block + ip6header + ip6 + ip6block

        # Write the RBLDNSD config file to disk
        src_path = r'output/'+ domain.replace(".","-")+".staging"
        dst_path = r'output/'+ domain.replace(".","-")
        with open(src_path, 'w') as fp:
            for item in myrbldnsdconfig:
                # write each item on a new line
                fp.write("%s\n" % item)
            print('Generating rbldnsd config for SPF records in ' + domain)
            print("Your domain " + domain + " required " + str(depth) + " lookups.")
        shutil.move(src_path, dst_path) 
    print("Waiting " + str(delayBetweenRun) + " seconds before running again... ")
    sleep(int(delayBetweenRun)) # wait DELAY before running again.