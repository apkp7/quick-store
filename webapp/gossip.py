import coreapi
from django.shortcuts import render
from .models import AffinityGroupView, Contact, Filetuple, Counter
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

@csrf_exempt
def listen_heartbeat(request):
    body = json.loads(request.body.decode('utf-8'))
    # pdb.set_trace()
    for node in body['nodes']:
        if node["IP"] != my_ip:
            node_from_db = AffinityGroupView.objects.filter(IP=node["IP"])
            if not node_from_db:
                # TODO: raise node failure alarm?
                new_node = AffinityGroupView(
                                IP=node["IP"],
                                port=node["port"],
                                heartbeatCount=node["heartbeatCount"],
                                rtt=0.0,
                                timestamp=Counter.objects.get(name='heartbeat').count
                            )
                new_node.save()
            elif node_from_db[0].heartbeatCount < node["heartbeatCount"]:
                node_from_db[0].heartbeatCount = node["heartbeatCount"]
                node_from_db[0].timestamp = Counter.objects.get(name='heartbeat').count
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
                                timestamp=Counter.objects.get(name='heartbeat').count
                            )
                new_filetuple.save()
            elif filetuple_from_db[0].heartbeatCount < filetuple["heartbeatCount"]:
                filetuple_from_db[0].heartbeatCount = filetuple["heartbeatCount"]
                filetuple_from_db[0].timestamp = Counter.objects.get(name='heartbeat').count
                filetuple_from_db[0].save()
    TTL = int(body['TTL'])
    disseminate_heartbeat(TTL - 1, body)
    return HttpResponse(str(TTL), status=200)
