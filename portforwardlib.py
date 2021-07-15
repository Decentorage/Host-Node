#!/usr/bin/python

# Utility to forward ports on your router using UPnP
# most code from  http://mattscodecave.com/posts/using-python-and-upnp-to-forward-a-port
# - adapted for command line use
# - support multiple routers in the lan

import socket
import re
from urllib.parse import urlparse
import urllib.request, urllib.parse, urllib.error
from xml.dom.minidom import parseString
from xml.dom.minidom import Document
import http.client
import time
import sys

def discover():
    """Discover UPNP capable routers in the local network
    Returns a lit of urls with service descriptions
    """
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_MX = 2
    SSDP_ST = "urn:schemas-upnp-org:device:InternetGatewayDevice:1"

    WAIT = 1

    ssdpRequest = "M-SEARCH * HTTP/1.1\r\n" + \
                    "HOST: %s:%d\r\n" % (SSDP_ADDR, SSDP_PORT) + \
                    "MAN: \"ssdp:discover\"\r\n" + \
                    "MX: %d\r\n" % (SSDP_MX, ) + \
                    "ST: %s\r\n" % (SSDP_ST, ) + "\r\n"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(0)
    sock.sendto(ssdpRequest.encode(), (SSDP_ADDR, SSDP_PORT))
    time.sleep(WAIT)
    paths = []
    for _ in range(10):
        try:
            data, fromaddr = sock.recvfrom(1024)
            #ip = fromaddr[0]
            #print "from ip: %s"%ip
            parsed = re.findall(r'(?P<name>.*?): (?P<value>.*?)\r\n', str(data,'utf-8'))

            # get the location header
            location = [x for x in parsed if x[0].lower() == "location"]

            # use the urlparse function to create an easy to use object to hold a URL
            router_path = location[0][1]
            paths.append(router_path)

        except socket.error:
            '''no data yet'''
            break

    #print(router_path)
    #print(paths)
    return paths


def get_wanip_path(upnp_url):
    # get the profile xml file and read it into a variable
    print("upnp_url ",upnp_url)
    directory = urllib.request.urlopen(upnp_url).read()
    print("directory ", directory)
    # create a DOM object that represents the `directory` document
    dom = parseString(directory)
    print("dom ", dom)
    # find all 'serviceType' elements
    service_types = dom.getElementsByTagName('serviceType')
    print("service types ", service_types)
    # iterate over service_types until we get either WANIPConnection
    # (this should also check for WANPPPConnection, which, if I remember correctly
    # exposed a similar SOAP interface on ADSL routers.
    for service in service_types:
        # I'm using the fact that a 'serviceType' element contains a single text node, who's data can
        # be accessed by the 'data' attribute.
        # When I find the right element, I take a step up into its parent and search for 'controlURL'
        print(service.childNodes[0].data)
        if (service.childNodes[0].data.find('WANIPConnection') > 0 ) or (service.childNodes[0].data.find('WANPPPConnection') > 0):
            path = service.parentNode.getElementsByTagName('controlURL')[0].childNodes[0].data
            return path, service.childNodes[0].data


def open_port(service, service_url, external_port, internal_client, internal_port=None, protocol='TCP', duration=0, description=None, enabled=1):
    print("service url ", service_url)
    parsedurl = urlparse(service_url)
    print("parsed url ", parsedurl.path)
    print("ssservice", service)
    if internal_port==None:
        internal_port = external_port

    if description == None:
        description = 'generated by port-forward.py'

    if not enabled:
        duration=1

    doc = Document()

    # create the envelope element and set its attributes
    envelope = doc.createElementNS('', 's:Envelope')
    envelope.setAttribute('xmlns:s', 'http://schemas.xmlsoap.org/soap/envelope/')
    envelope.setAttribute('s:encodingStyle', 'http://schemas.xmlsoap.org/soap/encoding/')

    # create the body element
    body = doc.createElementNS('', 's:Body')

    # create the function element and set its attribute
    fn = doc.createElementNS('', 'u:AddPortMapping')
    fn.setAttribute('xmlns:u', service)

    # setup the argument element names and values
    # using a list of tuples to preserve order
    arguments = [
        ('NewRemoteHost', ""), # unused - but required
        ('NewExternalPort', external_port),           # specify port on router
        ('NewProtocol', protocol),                 # specify protocol
        ('NewInternalPort', internal_port),           # specify port on internal host
        ('NewInternalClient', internal_client), # specify IP of internal host
        ('NewEnabled', enabled),                    # turn mapping ON
        ('NewPortMappingDescription', description), # add a description
        ('NewLeaseDuration', duration)]              # how long should it be opened?

    # NewEnabled should be 1 by default, but better supply it.
    # NewPortMappingDescription Can be anything you want, even an empty string.
    # NewLeaseDuration can be any integer BUT some UPnP devices don't support it,
    # so set it to 0 for better compatibility.

    # container for created nodes
    argument_list = []

    # iterate over arguments, create nodes, create text nodes,
    # append text nodes to nodes, and finally add the ready product
    # to argument_list
    for k, v in arguments:
        v = str(v)
        tmp_node = doc.createElement(k)
        tmp_text_node = doc.createTextNode(v)
        tmp_node.appendChild(tmp_text_node)
        argument_list.append(tmp_node)

    # append the prepared argument nodes to the function element
    for arg in argument_list:
        fn.appendChild(arg)

    # append function element to the body element
    body.appendChild(fn)

    # append body element to envelope element
    envelope.appendChild(body)

    # append envelope element to document, making it the root element
    doc.appendChild(envelope)

    # our tree is ready, conver it to a string
    pure_xml = doc.toxml()
    print("pure xml ", pure_xml)
    # use the object returned by urlparse.urlparse to get the hostname and port

    print("parsedurl.hostname :", parsedurl.hostname)
    print("parsedurl.port :", parsedurl.port)
    conn = http.client.HTTPConnection(parsedurl.hostname, parsedurl.port)

    # use the path of WANIPConnection (or WANPPPConnection) to target that service,
    # insert the xml payload,
    # add two headers to make tell the server what we're sending exactly.
    conn.request('POST',
        parsedurl.path,
        pure_xml,
        {'SOAPAction': service+'#AddPortMapping',
         'Content-Type': 'text/xml'}
    )

    # wait for a response
    resp = conn.getresponse()

    return resp.status, resp.read()


def get_my_ip(routerip=None):
    if routerip==None:
        routerip="8.8.8.8" #default route
    ret = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((routerip,80))
        ret = s.getsockname()[0]
        s.close()
    except:
        pass
    return ret

def forwardPort(eport, iport, router, lanip, disable, protocol, duration, description, verbose):

    if verbose:
        print("Discovering routers...")

    res = discover()
    timeout = time.time() + 10
    while len(res) == 0 and time.time() < timeout:
        res = discover()

    print(res)

    allok = False
    for path in res:
        discparsed = urlparse(path)
        service_path, service = get_wanip_path(path)
        print("discparsed.scheme ", discparsed.scheme)
        print("discparsed.netloc ", discparsed.netloc)
        print("service_path ", service_path)
        service_url = "%s://%s%s"%(discparsed.scheme,discparsed.netloc,service_path)
        routerip = discparsed.netloc.split(':')[0]
        print(routerip)
        if router !=None and routerip not in router:
            print("continue")
            continue

        localip = lanip
        if lanip == None:
            localip = get_my_ip(routerip)
            print("router ip", routerip)
            print("localip ", localip )
        enabled = int(not disable)

        dis=''
        if not enabled:
            dis='disable of '

        status, message = open_port(service, service_url, eport, internal_client=localip, internal_port=iport,
                                   protocol=protocol, duration=duration, description=description, enabled=enabled)
        print("status", status)
        print("message", message)
        if status==200:
            allok = True
            if verbose:
                print(("%sport forward on %s successful, %s->%s:%s"%(dis,routerip, eport,localip,iport)))
        else:
            sys.stderr.write("%sport forward on %s failed, status=%s message=%s\n"%(dis,routerip,status,message))
            allok = False


    return allok