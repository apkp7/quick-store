import coreapi
from django.shortcuts import render
from rest_framework import viewsets
from .models import AffinityGroupView, Contact, Filetuple, File
from .serializers import AffinityGroupViewSerializer, ContactSerializer, FiletupleSerializer, FileUploadSerializer, FileDownloadSerializer
from rest_framework import generics
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.utils.encoding import smart_str
import random 
import requests
from django.conf import settings
from django.http import FileResponse
import os


# Create your views here.
class AffinityGroupViewEndpoint(viewsets.ModelViewSet):
    queryset = AffinityGroupView.objects.all()
    serializer_class = AffinityGroupViewSerializer

class ContactEndpoint(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

class FiletupleEndpoint(viewsets.ModelViewSet):
    serializer_class = FiletupleSerializer
    queryset = Filetuple.objects.all()

class FileUtility:
    http = "http://"
    path_search_node = "/admin/webapp/search-node/?groupID="
    path_get_affinity_group_view = "/AffinityGroupView/"
    path_get_filetuple = "/Filetuple/"

    def loadBalancer(self,affinityGroups,fileTuple ):
        # Finding the affinity group with least number of files on it.
        import pdb; pdb.set_trace()
        affinityGroupsValue = affinityGroups.json()
        files = fileTuple.json()
        file_affinityGroupMapping = dict()
        for item in affinityGroupsValue:
            ip = item['IP']
            file_affinityGroupMapping[ip] = 0
        for file in files:
            ip = file['IP']
            file_affinityGroupMapping[ip] = file_affinityGroupMapping[ip] + 1
        
        file_affinityGroupMapping = sorted(file_affinityGroupMapping.items(), key=lambda x: x[1])
        print("The node with minimum load is :" + str(file_affinityGroupMapping[0][0]))
        ip = file_affinityGroupMapping[0][0]
        for item in affinityGroupsValue:
            if item['IP'] == ip:
                return item

    def hash(self,filename):
        s = 0
        for i in filename:
            s += ord(i)
        return s%3

    def get_node_from_destination_affinityGroup(self,param):
        hashValue = param
        #finding the target affinity group for file. 
        target_group = Contact.objects.all().filter(groupID = hashValue)
        return target_group.values()[0]   
    
    def get_file_homenode(self,affinityGroup_node_contact):
        ip = affinityGroup_node_contact['IP']
        port = affinityGroup_node_contact['port']
        result = []
        try:
            affinityGroups = requests.get(self.http + ip + ":"+ port + self.path_get_affinity_group_view)
            fileTuple = requests.get(self.http + ip + ":"+ port + self.path_get_filetuple)
        except Exception as e:
            print(e)
        home_node = self.loadBalancer(affinityGroups,fileTuple)

        return home_node

class SearchNode(generics.ListAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        queryset = Contact.objects.all()
        param = self.request.query_params.get('groupID','')
        result = queryset.filter(groupID = param)
        return result

class GetAffinityGroup(APIView,FileUtility):

    def get(self,request):
        queryset = Contact.objects.all()
        param = self.request.query_params.get('groupID','')
        result = self.get_node_from_destination_affinityGroup(param)
        serializer = ContactSerializer
        result = serializer(result).data
        return Response(result)

class GetFiletuple(generics.ListAPIView):

    serializer_class = FiletupleSerializer
    def get_queryset(self):
        queryset = Filetuple.objects.all()
        param = self.request.query_params.get('fileName','')
        result = queryset.filter(fileName = param)
        return result

class Ping(APIView):
    def get(self,reuest):
        return HttpResponse(status=200)

class SaveFile(APIView):

    def get(self,request):
        queryset = File.objects.all()
        param = self.request.query_params.get('fileName','')
        result = queryset.filter(file_name = param)
        if not result:
            return HttpResponse(status=404) 
        else:
            file_name = result[0].file_name
            path_to_file = os.path.join(settings.MEDIA_ROOT,file_name)
            response = FileResponse(open(path_to_file, 'rb'), as_attachment=False)
            return response

    def post(self,request):
        serializer = FileUploadSerializer(data = request.data )
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(status=201)
        return HttpResponse(status = 500)

class UploadFile(APIView,FileUtility):
    http = "http://"
    path_search_node = "/admin/webapp/search-node/?groupID="
    path_get_affinity_group_view = "/AffinityGroupView/"
    path_save_file = "/admin/webapp/save-file/"
    path_add_filetuple = "/Filetuple/"
    shared_file_storage = ""

    def post(self,request):
        myfile = request.data['file_obj']
        filename = request.data['file_name']
        myfile.name  = filename
        serializer = FileUploadSerializer(data = request.data )
        if not serializer.is_valid():
            return HttpResponse(status=400)

        groupID = self.hash(filename)
        print("*"*50)
        print("-----------  The destination group of file is: " + str(groupID) + "---------------")
        print("*"*50)

        node_destination_affinityGroup = self.get_node_from_destination_affinityGroup(groupID)
        if node_destination_affinityGroup:
            file_homenode = self.get_file_homenode(node_destination_affinityGroup)
            if not file_homenode:
                return HttpResponse(status=500)
            else:
                ip = file_homenode['IP']
                port = file_homenode['port']

                print("*"*50)
                print("--------------  The home node is file is IP: " + str(ip)  + "---------------")
                print("*"*50)

                values = {'file_name' : filename}
                url_file = self.http + str(ip) + ":"+ str(port) + self.path_save_file
                files = {'file_obj': request.data['file_obj']}
                url_file_tuple = self.http + str(ip) + ":"+ str(port) + self.path_add_filetuple
                data = {"fileName" : filename, "IP" : str(ip),  "port" : str(port), "heartbeatCount" : "0", "timestamp": "0"}
                try:
                    result = requests.post(url_file ,files=files , data =values)
                    response = requests.post(url_file_tuple, data = data) 
                except Exception as e:
                    print(e)
                    return HttpResponse(status = 500)
                else:
                    if result.status_code == 201:
                        print("*"*50)
                        print("----------------- File uploaded successfully  --------------")
                        print("*"*50)
                        return HttpResponse(status = 201)
                    else:
                        return HttpResponse(status = result.status_code)
        return HttpResponse(status = 500)

class DownloadFile(APIView,FileUtility):

    path_save_file = "/admin/webapp/save-file"
    path_get_file_touple = "/admin/webapp/get-file/"
    def get(self,request):
        filename = self.request.query_params.get('fileName','')
        groupID = self.hash(filename)
        print("The destination group of file is: " + str(groupID))
        node_destination_affinityGroup = self.get_node_from_destination_affinityGroup(groupID)
        if node_destination_affinityGroup:
            ip = node_destination_affinityGroup['IP']
            port = node_destination_affinityGroup['port']
            try:
                file_home_node = requests.get(self.http + ip + ":"+ port + self.path_get_file_touple +"?fileName="+ filename)
                file_home_node = file_home_node.json()
            except Exception as e:
                print(e)
                return HttpResponse(status = 500)

            if not file_home_node:
                return HttpResponse(status=404)
            else:
                print("The node which holds the file is: " + str(file_home_node[0]['IP']))
                ip = file_home_node[0]['IP']
                port = file_home_node[0]['port']
                url = self.http + str(ip) + ":"+ str(port) + self.path_save_file +"?fileName="+ filename
                try:
                    result = requests.get(url)
                except Exception as e:
                    print(e)
                    return HttpResponse(status = 404)
                else:
                    # import pdb; pdb.set_trace()
                    if result.status_code == 200:
                        path_to_file = os.path.join(settings.MEDIA_ROOT ,'download')
                        path_to_file = os.path.join(path_to_file,filename)
                        file = open(path_to_file, "wb")
                        file.write(result.content)
                        file.close()
                        print("Downloaded the file successfully")
                        return HttpResponse(status = 200)
                    else:
                        return HttpResponse(status = result.status_code)
        return HttpResponse(status = 500)

