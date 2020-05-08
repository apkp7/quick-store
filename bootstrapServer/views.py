
from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
import requests

nodeIps = []
port = "8000"

def getActiveList():
    activeList = " Active node in network are :- "
    for IP in nodeIps:
        activeList += IP + " , "
    return HttpResponse(activeList ,status=200)

def index(request, hostIp):

    #case when no node is present.
    message = " Failed to join node " + hostIp
    status = 400
    if hostIp == "getActiveList":
        return getActiveList()

    if len(nodeIps) == 0:
        #call api to create affenty group and first node.
        url = "http://" + hostIp + ":" + port + "/admin/webapp/add_first_node"
        try:
            result = requests.post(url, data={"nodeIp" : hostIp, "port" : port})
            if(result.status_code == 200):
                nodeIps.append(hostIp)
                message = "First node added in network IP = " + hostIp
                status = result.status_code
        except Exception as ex:
            print(ex)
        return HttpResponse(message,status=status)

    activeIP = ""
    for ip in nodeIps:
        #check if node is alive if yes then re-route call.
        url = "http://" + ip + ":" + port + "/admin/webapp/check_node"
        r = requests.get(url)
        if r.status_code == 200:
            activeIP = ip
            break
        else:
            nodeIps.remove(ip)
    url = "http://" + activeIP + ":" + port + "/admin/webapp/add_node"
    try:
        result = requests.post(url, data={"newNodeIp" : hostIp, "existingNodeIp" : activeIP, "port" : port})
        if result.status_code == 200:
            nodeIps.append(hostIp)
            message = "Node with IP =  " + hostIp + " ,Port =" + port + " added to P2P network."
            status = result.status_code
    except Exception as ex:
        print(ex)

    return HttpResponse(message,status=status)