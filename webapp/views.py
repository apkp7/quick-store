import coreapi
from django.shortcuts import render
from rest_framework import viewsets
from .models import AffinityGroupView, Contact, Filetuple, Counter
from .serializers import AffinityGroupViewSerializer, ContactSerializer, FiletupleSerializer
from rest_framework import generics
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
import random
import requests


# Create your views here.
class AffinityGroupViewEndpoint(viewsets.ModelViewSet):
    queryset = AffinityGroupView.objects.all()
    serializer_class = AffinityGroupViewSerializer

class ContactEndpoint(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

class FiletupleEndpoint(viewsets.ModelViewSet):

    queryset = Filetuple.objects.all()
    serializer_class = FiletupleSerializer

class SearchNode(generics.ListAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        queryset = Contact.objects.all()
        param = self.request.query_params.get('groupID','')
        result = queryset.filter(groupID = param)
        return result

class InsertFile(APIView):
    http = "http://"
    path_search_node = "/admin/webapp/search-node/?groupID="
    path_get_affinity_group_view = "/AffinityGroupView/"
    shared_file_storage = ""
    def hash(self,filename):
        s = 0
        for i in filename:
            s += ord(i)
        return 4
    #returns a node which present in the affinity group of file destination.
    def get_node_from_destination_affinityGroup(self,param):
        print(param)
        hashValue = self.hash(param)
        print(hashValue)

        #finding the target affinity group for file.
        target_group = Contact.objects.all().filter(groupID = hashValue).order_by('rtt')
        result = []
        if not target_group:  # group info not present at current node.
            client = coreapi.Client()
            queryset = AffinityGroupView.objects.all()
            
            for node in queryset:
                print(node)
                ip = node.IP
                port = node.port
                print(ip)
                try:
                    result = requests.get(self.http + ip + ":"+ port + self.path_search_node + str(hashValue),timeout =(0.1,1))
                    print("finding the node in destination contact")
                    print(result)
                except Exception as e:
                    print(e)
                else:
                    break
        if result:
            return result.json()
        else:
            return list()
    
    def get_file_homenode(self,affinityGroup_node_contact):
        print(affinityGroup_node_contact)
        ip = affinityGroup_node_contact['IP']
        port = affinityGroup_node_contact['port']
        result = []
        try:
            result = requests.get(self.http + ip + ":"+ port + self.path_get_affinity_group_view)
        except Exception as e:
            print(e)
        home_node = random.choice(result.json())
        return home_node        

    def get(self,request):
        param = self.request.query_params.get('fileName','')
        node_destination_affinityGroup = self.get_node_from_destination_affinityGroup(param)
        print("got the result in get api")
        print(node_destination_affinityGroup)
                    
        if node_destination_affinityGroup:
            file_homenode = self.get_file_homenode(dict(node_destination_affinityGroup[0]))
            if not file_homenode:
                return HttpResponse(message="Home node not found",status=500)
            else:
                return HttpResponse(status=404)
    