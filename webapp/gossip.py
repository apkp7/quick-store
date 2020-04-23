import coreapi
from django.shortcuts import render
from .models import AffinityGroupView, Contact, Filetuple, Misc
from .serializers import AffinityGroupViewSerializer, ContactSerializer, FiletupleSerializer
from .tasks import disseminate_heartbeat
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import random
import requests
from celery import Celery
import sys
import json 
import pdb

# TODO: create one model for my_ip
my_ip = requests.get('https://api.ipify.org').text
my_group_id = Misc.objects.get(name='heartbeat').groupID

@csrf_exempt
def listen_heartbeat(request):
    body = json.loads(request.body.decode('utf-8'))
    curr_time = Misc.objects.get(name='heartbeat').count
    for node in body['nodes']:
        if node["IP"] != my_ip:
            node_from_db = AffinityGroupView.objects.filter(IP=node["IP"])
            if not node_from_db:
                new_node = AffinityGroupView(
                                IP=node["IP"],
                                port=node["port"],
                                heartbeatCount=node["heartbeatCount"],
                                rtt=0.0,
                                timestamp=curr_time
                            )
                new_node.save()
            else:
                if node_from_db[0].heartbeatCount < node["heartbeatCount"]:
                    node_from_db[0].heartbeatCount = node["heartbeatCount"]
                    node_from_db[0].timestamp = curr_time
                    node_from_db[0].isFailed = False                
                    node_from_db[0].save()
                elif node["isFailed"]:
                    node_from_db[0].isFailed = True
                    node_from_db[0].save()
    for contact in body['contacts']:
        if contact["IP"] != my_ip and contact['actual']:
            node_from_db = Contact.objects.filter(IP=contact["IP"])
            if not node_from_db:
                new_node = Contact(
                                groupID=contact["groupID"],
                                IP=contact["IP"],
                                port=contact["port"],
                                heartbeatCount=contact["heartbeatCount"],
                                rtt=0.0,
                                timestamp=curr_time
                            )
                new_node.save()
            else:
                if node_from_db[0].heartbeatCount < contact["heartbeatCount"]:
                    node_from_db[0].heartbeatCount = contact["heartbeatCount"]
                    node_from_db[0].timestamp = curr_time
                    node_from_db[0].isFailed = False                
                    node_from_db[0].save()
                elif contact["isFailed"]:
                    node_from_db[0].isFailed = True
                    node_from_db[0].save()
    for filetuple in body['filetuples']:
        if filetuple["IP"] != my_ip:
            # TODO: enforce unique filenames?
            filetuple_from_db = Filetuple.objects.filter(fileName=filetuple["fileName"])
            if not filetuple_from_db:
                new_filetuple = Filetuple(
                                IP=filetuple["IP"],
                                port=filetuple["port"],
                                heartbeatCount=filetuple["heartbeatCount"],
                                fileName=filetuple["fileName"],
                                timestamp=curr_time
                            )
                new_filetuple.save()
            else:
                if filetuple_from_db[0].heartbeatCount < filetuple["heartbeatCount"]:
                    filetuple_from_db[0].heartbeatCount = filetuple["heartbeatCount"]
                    filetuple_from_db[0].timestamp = curr_time
                    filetuple_from_db[0].isFailed = False                
                    filetuple_from_db[0].save()
                elif filetuple["isFailed"]:
                    filetuple_from_db[0].isFailed = True
                    filetuple_from_db[0].save()
    print("\n"+"*"*75)
    print("----------- Gossip stream: Membership list updated ---------------")
    print("----------- Gossip stream: Local contact list updated ---------------")
    print("----------- Gossip stream: Filetuple list updated ---------------")
    print("*"*75 +"\n")
    TTL = int(body['TTL'])
    disseminate_heartbeat(TTL - 1, body)
    return HttpResponse(str(TTL), status=200)



@csrf_exempt
def intergroup_hearbeat(request):
    body = json.loads(request.body.decode('utf-8'))
    for node in body['contacts']:
        if node["groupID"] != my_group_id and node["IP"] != my_ip:
            node_from_db = Contact.objects.filter(IP=node["IP"])
            curr_time = Misc.objects.get(name='heartbeat').count
            if not node_from_db:
                new_node = Contact(
                                groupID=node["groupID"],
                                IP=node["IP"],
                                port=node["port"],
                                heartbeatCount=node["heartbeatCount"],
                                rtt=0.0,
                                timestamp=curr_time,
                                actual=True
                            )
                new_node.save()
            elif node_from_db[0].heartbeatCount < node["heartbeatCount"]:
                node_from_db[0].heartbeatCount = node["heartbeatCount"]
                node_from_db[0].timestamp = curr_time
                node_from_db[0].save()
    print("\n"+ "*"*75)
    print("----------- Gossip stream: Contact list updated ---------------")
    print("*"*75 +"\n")
    return HttpResponse(status=200)



@csrf_exempt
def delete_node(request):
    body = json.loads(request.body.decode('utf-8'))
    for node_ip in body['nodes']:
        AffinityGroupView.objects.filter(IP=node_ip, isFailed=True).delete()
        Filetuple.objects.filter(IP=node_ip, isFailed=True).delete()
        print("\n"+ "*"*75)
        print("----------- Failure detection: " + str(node_ip) + " node deleted from membership list ---------------")
        print("*"*75 +"\n")
    for contact_ip in body['contacts']:
        Contact.objects.filter(IP=contact_ip, isFailed=True).delete()
        print("\n"+ "*"*75)
        print("----------- Failure detection: " + str(contact_ip) + " contact deleted from membership list ---------------")
        print("*"*75 +"\n")
    return HttpResponse(status=200)
