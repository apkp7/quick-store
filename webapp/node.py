from .models import AffinityGroupView, Contact, Filetuple, Misc
from django.http import HttpResponse
import hashlib
import requests
# k = number of affinity groups in system
k = 3

def getHashValue(ip):
    encodedIp = hashlib.sha1(ip.encode())
    hexaValue = encodedIp.hexdigest()
    hashString = hexaValue[0:5]
    asciiValue = 0
    for char in hashString:
        asciiValue += ord(char)
    return asciiValue%k

def check_node(request):
    return HttpResponse("Application alive",status=200)

#api to add first node in a new affinity group
def add_first_node(request):
    ip = request.form["nodeIp"]
    port = request.form["port"]
    groupId = getHashValue(ip)
    node = AffinityGroupView.objects.create(IP=ip, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
    contact = Contact.objects.create( groupID=groupId, IP=ip, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)

def add_node(request):
    newNodeIp = request.form["newNodeIp"]
    existingNodeIp = request.form["existingNodeIp"]
    port = request.form["port"]
    newNodeGroupId = getHashValue(newNodeIp)
    existingNodeGroupId = getHashValue(existingNodeIp)

    #case when new node is of same affinity group
    if newNodeGroupId == existingNodeGroupId:
        node = AffinityGroupView.objects.create(IP=newNodeIp, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
        return HttpResponse("Node added in affinity group",status=201)

    #case when new affinity group do not exists or node belong to different affinity group then current node
    if newNodeGroupId != existingNodeGroupId:
        #get list of all nodes which are in the new node affinity group.
        target_group = Contact.objects.all().filter(groupID = newNodeGroupId).order_by('rtt')
        #If this affinity group does not exists
        if not target_group:
            add_new_affinity_group(newNodeIp,newNodeGroupId,port)
        else:
            contactNodeIP = target_group[0].IP
            add_node_in_existing_affinity_group(newNodeIp, contactNodeIP, port)
    return HttpResponse("Node added ",status=201)

def add_new_affinity_group(newNodeIp, newNodeGroupId, port):
    #create contact at current node and call add new node method.
    contact = Contact.objects.create(groupID=newNodeGroupId, IP=newNodeIp, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
    url = "http://" + newNodeIp + ":" + port + "/admin/webapp/add_first_node"
    try:
        result = requests.post(url, json={"nodeIp" : newNodeIp, "port" : port})
    except Exception as ex:
        print(ex)
    return HttpResponse("New affinity group added in network IP = " + newNodeIp, status=201)

def add_node_in_existing_affinity_group(newNodeIp, contactNodeIP, port):
    url = "http://" + contactNodeIP + ":" + port + "/admin/webapp/add_node"
    try:
        result = requests.post(url, json={"newNodeIp" : newNodeIp, "existingNodeIp" : contactNodeIP, "port" : port})
    except Exception as ex:
        print(ex)
    return HttpResponse("Node added in affinity group, IP = " + newNodeIp, status=201)