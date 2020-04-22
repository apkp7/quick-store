from .models import AffinityGroupView, Contact, Filetuple, Misc
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import hashlib
import requests
import pdb

my_ip = requests.get('https://api.ipify.org').text

# number of affinity groups in system
totalNumberOfGroups = 3
# Set status code to 200 in case request is processed with out error


def getHashValue(ip):
    # encodedIp = hashlib.sha1(ip.encode())
    # hexaValue = encodedIp.hexdigest()
    # hashString = hexaValue[0:5]
    # asciiValue = 0
    # for char in hashString:
    #     asciiValue += ord(char)
    # return asciiValue%totalNumberOfGroups
    return 2



def check_node(request):
    return HttpResponse("Application alive",status=200)


@csrf_exempt
def update_groupId_in_misc(request):
    pdb.set_trace()
    misc = Misc.objects.get(name = "heartbeat")
    misc.groupID = getHashValue(my_ip)
    misc.save()
    return HttpResponse(status=200)


#api to add first node in a new affinity group
@csrf_exempt
def add_first_node(request):
    ip = request.POST.get('nodeIp','')
    port = request.POST.get('port','')
    groupId = getHashValue(ip)

    AffinityGroupView.objects.create(IP=ip, port=port)
    Contact.objects.create(groupID=groupId, IP=ip, port=port, actual = True)
    misc = Misc.objects.get(name = "heartbeat")
    misc.groupID = groupId
    misc.save()
    return HttpResponse("First Node, IP " + ip + " in Affinity Group " + str(groupId) + " added",status=200)




@csrf_exempt
def add_node(request):
    newNodeIp = request.POST.get('newNodeIp','')
    existingNodeIp = request.POST.get('existingNodeIp','')
    port = request.POST.get('port','')
    newNodeGroupId = getHashValue(newNodeIp)

    existingNodeGroupId = 1
    message = "Failed to add new node IP " + newNodeIp
    status = 400
    #case when new node is of same affinity group
    if newNodeGroupId == existingNodeGroupId:
        try:
            requests.post("http://" + newNodeIp + ":" + port+ "/admin/webapp/update_groupid")
        except Exception as ex:
            print(ex)
        AffinityGroupView.objects.create(IP=newNodeIp, port=port)
        return HttpResponse("Node with IP = " + newNodeIp +" added in affinity group " + str(newNodeGroupId), status=200)

    #case when new affinity group do not exists or node belong to different affinity group then current node
    if newNodeGroupId != existingNodeGroupId:
        #get list of all nodes which are in the new node affinity group.
        target_group = Contact.objects.filter(groupID=str(newNodeGroupId)).order_by('rtt')
        #If this affinity group does not exists
        if not target_group:
            contact = Contact.objects.filter(groupID=existingNodeGroupId)
            if contact:
                contact = contact[0]
                url = "http://"+ contact.IP + ":" + contact.port + "/Contact/"
                data = {'groupID': str(newNodeGroupId) , 'IP': newNodeIp, 'port': '8000', 'actual' : True}
                try:
                    response = requests.post(url , data = data )
                except Exception as e:
                    print(e)        
                status = add_new_affinity_group(newNodeIp,newNodeGroupId,port)
                if status == 200:
                    message = "New affinity group + " + str(newNodeGroupId) + " added in network IP = " + newNodeIp
        else:
            pdb.set_trace()
            contactNodeIP = target_group[0].IP
            contactNodePort = target_group[0].port
            status = add_node_in_existing_affinity_group(newNodeIp, port, contactNodeIP, contactNodePort)
            if status == 200:
                message = "New node IP = " + newNodeIp + " ,affinity group + " + str(newNodeGroupId) + " added in network"
    return HttpResponse(message,status=status)




@csrf_exempt
def add_new_affinity_group(newNodeIp, newNodeGroupId, port):
    status = 400
    url = "http://" + newNodeIp + ":" + port + "/admin/webapp/add_first_node"
    try:
        result = requests.post(url, data={"nodeIp" : newNodeIp, "port" : port})
        status = result.status_code
    except Exception as ex:
        print(ex)
    return status




@csrf_exempt
def add_node_in_existing_affinity_group(newNodeIp, newNodePort, contactNodeIP, contactNodePort):
    status = 400
    url = "http://" + contactNodeIP + ":" + port + "/admin/webapp/add_node"
    try:
        result = requests.post(url, data={"newNodeIp" : newNodeIp, "existingNodeIp" : contactNodeIP, "port" : port})
        status = result.status_code
    except Exception as ex:
        print(ex)
    return status
