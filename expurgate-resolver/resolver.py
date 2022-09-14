# author: https://github.com/smck83/
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
    source_prefix = ['_xpg8'] #if not specified, store your 'hidden' record at _xpg8.<yourdomain>
if 'MY_DOMAINS' in os.environ:
    domains = os.environ['MY_DOMAINS']
    mydomains = domains.split(' ') # convert input string to list
    mydomains = [domain for domain in mydomains if '.' in domain] # confirm domain contains a fullstop
    mydomains = list(dict.fromkeys(mydomains)) # dedupe the list of domains
else:
    source_prefix_off = True
    mydomains = ['google.com','mimecast.com','microsoft.com','github.com','who.int','apple.com'] # demo mode
    print("MY_DOMAIN not set, running in demo mode using " + str(mydomains))
if 'DELAY' in os.environ and int(os.environ['DELAY']) > 29:
    delayBetweenRun = os.environ['DELAY']
else:
    delayBetweenRun = 300 #default to 5 minutes
print("Running delay of : " + str(delayBetweenRun))
totaldomaincount = len(mydomains)

def dnsLookup(domain,type):
    global depth
    try:
        lookup = [dns_record.to_text() for dns_record in dns.resolver.resolve(domain, type).rrset]
        depth += 1
        return lookup
    except:
        print("DNS Resolution Error - " + type + ":" + domain)
        header.append("# DNS Resolution Error - " + type + ":" + domain)
    
    

def getSPF(domain):
    global depth
    try:
        #try:
        if depth == 0 and source_prefix_off == False:
           sourcerecord = source_prefix + "." + domain
           result = dnsLookup(sourcerecord,"TXT")
        else:
           result = dnsLookup(domain,"TXT")      
   
    except:
        print("An exception occurred, check there is a DNS TXT record with SPF present at: " + str(source_prefix) + "." + str(domain) )
    if result:
        for record in result:
            if record != None and re.match('^"v=spf1 ', record, re.IGNORECASE):
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
                        getSPF(spfValue[1])
                    elif re.match('^(\+|)include\:', spfPart, re.IGNORECASE) and "%{" not in spfPart:
                        spfValue = spfPart.split(':')
                        if spfValue[1] != domain and spfValue[1] and spfValue[1] not in includes:
                            includes.append(spfValue[1])
                            getSPF(spfValue[1])
                        elif spfValue[1]:
                            header.append("# ERROR DETECTED: Invalid DNS Record, Loop or Duplicate: " + spfValue[1] + " in " + domain)
                            print("ERROR DETECTED: Invalid DNS Record, Loop or Duplicate: " + spfValue[1] + " in " + domain)
                    elif re.match('^(\+|)a\:', spfPart, re.IGNORECASE):
                        spfValue = spfPart.split(':')
                        result = dnsLookup(spfValue[1],"A")  
                        if result:
                            header.append("# " + ("^" * depth) + " " + spfPart)
                            result = [x + ' # a:' + spfValue[1] for x in result]
                            result.sort() # sort
                            result = ('\n').join(result)
                            ip4.append(result + " # " + spfPart)
                    elif re.match('^(\+|)a', spfPart, re.IGNORECASE):
                        result = dnsLookup(domain,"A")
                        if result:  
                            header.append("# " + ("^" * depth) + " " + spfPart + "(" + domain + ")")
                            result = [x + " # a(" + domain + ")" for x in result]
                            result.sort() # sort
                            result = ('\n').join(result)
                            ip4.append(result)
                    elif re.match('^(\+|)mx\:', spfPart, re.IGNORECASE):
                        spfValue = spfPart.split(':')
                        result = dnsLookup(spfValue[1],"MX") 
                        if result:    
                            header.append("# " + ("^" * depth) + " " + spfPart)   
                            myarray = []
                            for mxrecord in result:
                                mxValue = mxrecord.split(' ')
                                myarray.append(mxValue[1])
                            for hostname in myarray:
                                result = dnsLookup(hostname,"A")  
                                if result:
                                    result = [x + ' # ' + spfPart + '=>a:' + hostname for x in result]
                                    result.sort() # sort
                                    result = ('\n').join(result.sort)
                                    ip4.append(result)
                                    header.append("# " + ("^" * depth) + " " + spfPart + "=>a:" + hostname)

                    elif re.match('^(\+|)mx', spfPart, re.IGNORECASE):
                        result = dnsLookup(domain,"MX")
                        if result:
                            header.append("# " + ("^" * depth) + " mx(" + domain + ")")
                            print("Error performing MX lookup")
                            myarray = []
                            for mxrecord in result:
                                mxValue = mxrecord.split(' ')
                                myarray.append(mxValue[1])
                            for hostname in myarray:
                                result = dnsLookup(hostname,"A")  
                                if result:
                                    result = [x + ' # mx(' + domain + ')=>a:' + hostname for x in result ]
                                    result.sort() # sort
                                    result = ('\n').join(result)
                                    ip4.append(result)
                                    header.append("# " + ("^" * depth) + " mx(" + domain + ")=>a:" + hostname)

                    elif re.match('^(\+|)ip4\:', spfPart, re.IGNORECASE):
                        spfValue = spfPart.split('ip4:')
                        ip4.append(spfValue[1] + " # " + domain)
                    elif re.match('(\+|)ip6\:', spfPart, re.IGNORECASE):
                        spfValue = spfPart.split('ip6:')
                        ip6.append(spfValue[1] + " # " + domain)
                    elif re.match('[\+\-\~\?]all', spfPart, re.IGNORECASE):
                        spfAction.append(spfPart)
                    elif re.match('v\=spf1', spfPart, re.IGNORECASE):
                        spfValue = spfPart
                    else:
                        print('No match:',spfPart)
                        otherValues.append(spfPart)

while loop == 0 and mydomains:
    print('Generating config for SPF records in ' + str(mydomains))
    domaincount = 0
    for domain in mydomains:
        domaincount +=1
        
        datetimeNow = datetime.now(tz=None)
        header = ["# Automatically generated rbldnsd config by Expurgate[xpg8.tk] for:" + domain + " @ " + str(datetimeNow)]
        ip4 = []
        ip4header = []
        ip6 = []
        ip6header = []
        spfAction = ["~all"]
        otherValues = []
        depth = 0
        includes = []

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
            otherValues = list(dict.fromkeys(otherValues)) #dedupe
            ip4block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
            ip6block = [":99:v=spf1 " + ' '.join(otherValues) + " " + spfAction[0]]
        else:
            ip4block = [":99:v=spf1 " + spfAction[0]]
            ip6block = [":99:v=spf1 " + spfAction[0]]
        ip4block.append("0.0.0.0/1 # all other IPv4 addresses")
        ip4block.append("128.0.0.0/1 # all other IP IPv4 addresses")
        ip6header.append("$DATASET ip6trie:"+ domain +" " + domain + " @")
        ip6header.append(":3:v=spf1 ip6:$ " + spfAction[0])
        ip6block.append("0:0:0:0:0:0:0:0/0 # all other IPv6 addresses")
        # Join all the pieces together, ready for file output
        myrbldnsdconfig = header + ip4header + ip4 + ip4block + ip6header + ip6 + ip6block

        # Write the RBLDNSD config file to disk
        src_path = r'output/'+ domain.replace(".","-")+".staging"
        dst_path = r'output/'+ domain.replace(".","-")
        with open(src_path, 'w') as fp:
            for item in myrbldnsdconfig:
                # write each item on a new line
                fp.write("%s\n" % item)
            print('[' + str(domaincount) +'/'+ str(totaldomaincount) + '] Generating rbldnsd config for SPF records in ' + domain)
            print('[' + str(domaincount) +'/'+ str(totaldomaincount) + '] Your domain ' + domain + ' required ' + str(depth) + ' lookups.')
        shutil.move(src_path, dst_path) 
    print("Waiting " + str(delayBetweenRun) + " seconds before running again... ")
    sleep(int(delayBetweenRun)) # wait DELAY in secondsbefore running again.
