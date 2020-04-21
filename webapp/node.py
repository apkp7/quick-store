from .models import AffinityGroupView, Contact, Filetuple, Misc
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import hashlib
import requests
# number of affinity groups in system
totalNumberOfGroups = 3
# Set status code to 200 in case request is processed with out error

def getHashValue(ip):
    encodedIp = hashlib.sha1(ip.encode())
    hexaValue = encodedIp.hexdigest()
    hashString = hexaValue[0:5]
    asciiValue = 0
    for char in hashString:
        asciiValue += ord(char)
    return asciiValue%totalNumberOfGroups

@csrf_exempt
def check_node(request):
    return HttpResponse("Application alive",status=200)

#api to add first node in a new affinity group
@csrf_exempt
def add_first_node(request):
    ip = request.POST.get('nodeIp','')
    port = request.POST.get('port','')
    groupId = getHashValue(ip)
    print (" ip = " + ip + " port = " + port + " groupId  = " + str(groupId))
    newNode = AffinityGroupView(IP=ip, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
    newNode.save()
    newContact = Contact( groupID=groupId, IP=ip, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
    newContact.save()
    return HttpResponse("First Node, IP " + ip + " in Affinity Group " + str(groupId) + " added",status=200)

@csrf_exempt
def add_node(request):
    newNodeIp = request.POST.get('newNodeIp','')
    existingNodeIp = request.POST.get('existingNodeIp','')
    port = request.POST.get('port','')
    newNodeGroupId = getHashValue(newNodeIp)
    existingNodeGroupId = getHashValue(existingNodeIp)
    message = " Failed to add new node IP " + newNodeIp
    status = 400
    #case when new node is of same affinity group
    if newNodeGroupId == existingNodeGroupId:
        node = AffinityGroupView.objects.create(IP=newNodeIp, port=port, rtt=0.0, heartbeatCount=0, timestamp=0)
        return HttpResponse("Node with IP = " + newNodeIp +" added in affinity group " + str(newNodeGroupId), status=200)

    #case when new affinity group do not exists or node belong to different affinity group then current node
    if newNodeGroupId != existingNodeGroupId:
        #get list of all nodes which are in the new node affinity group.
        target_group = Contact.objects.all().filter(groupID = str(newNodeGroupId)).order_by('rtt')
        #If this affinity group does not exists
        if not target_group:
            status = add_new_affinity_group(newNodeIp,newNodeGroupId,port)
            if status == 200:
                message = "New affinity group + " + str(newNodeGroupId) + " added in network IP = " + newNodeIp
        else:
            contactNodeIP = target_group[0].IP
            status = add_node_in_existing_affinity_group(newNodeIp, contactNodeIP, port)
            if status == 200:
                message = "New node IP = " + newNodeIp + " ,affinity group + " + str(newNodeGroupId) + " added in network"
    return HttpResponse(message,status=status)

@csrf_exempt
def add_new_affinity_group(newNodeIp, newNodeGroupId, port):
    status = 400
    url = "http://" + newNodeIp + ":" + port + "/admin/webapp/add_first_node"
    try:
        result = requests.post(url, data={"nodeIp" : newNodeIp, "port" : port})
        if result.status_code == 200:
            #create contact at current node and call add new node method.
            contact = Contact.objects.create(
                groupID=newNodeGroupId,
                IP=newNodeIp,
                port=port,
                rtt=0.0,
                heartbeatCount=0,
                timestamp=0)
            status = result.status_code

    except Exception as ex:
        print(ex)
    return status

@csrf_exempt
def add_node_in_existing_affinity_group(newNodeIp, contactNodeIP, port):
    status = 400
    url = "http://" + contactNodeIP + ":" + port + "/admin/webapp/add_node"
    try:
        result = requests.post(url, data={"newNodeIp" : newNodeIp, "existingNodeIp" : contactNodeIP, "port" : port})
        if result.status_code == 200:
            status = result.status_code
    except Exception as ex:
        print(ex)
    return status