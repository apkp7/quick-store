import coreapi
from django.shortcuts import render
from rest_framework import viewsets
from .models import AffinityGroupView, Contact, Filetuple, Counter, File
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

    def hash(self,filename):
        s = 0
        for i in filename:
            s += ord(i)
        return 4

    def get_node_from_destination_affinityGroup(self,param):
        hashValue = self.hash(param)
        #finding the target affinity group for file. 
        target_group = Contact.objects.all().filter(groupID = hashValue).order_by('rtt')
        result = []
        if not target_group:  # group info not present at current node.
            queryset = AffinityGroupView.objects.all()            
            for node in queryset:
                ip = node.IP
                port = node.port
                try:
                    result = requests.get(self.http + ip + ":"+ port + self.path_search_node + str(hashValue),timeout =(0.1,1))
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

    def get_file_homenode_download(self,affinityGroup_node_contact):
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


class SearchNode(generics.ListAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        queryset = Contact.objects.all()
        param = self.request.query_params.get('groupID','')
        result = queryset.filter(groupID = param)
        return result


class GetFiletuple(generics.ListAPIView):

    serializer_class = FiletupleSerializer
    
    def get_queryset(self):
        queryset = Filetuple.objects.all()
        param = self.request.query_params.get('fileName','')
        print("parameter",param)
        result = queryset.filter(fileName = param)
        print(result)
        return result


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
            # import pdb; pdb.set_trace()
            response = FileResponse(open(path_to_file, 'rb'), as_attachment=False)
            return response

    def post(self,request):
        serializer = FileUploadSerializer(data = request.data )
        # import pdb; pdb.set_trace()
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(status=201)
        return HttpResponse(status = 500)

class UploadFile(APIView,FileUtility):
    http = "http://"
    path_search_node = "/admin/webapp/search-node/?groupID="
    path_get_affinity_group_view = "/AffinityGroupView/"
    path_save_file = "/admin/webapp/save-file/"
    shared_file_storage = ""

    def post(self,request):
        myfile = request.data['file_obj']
        filename = request.data['file_name']
        myfile.name  = filename
        serializer = FileUploadSerializer(data = request.data )
        if not serializer.is_valid():
            return HttpResponse(status=400)
        node_destination_affinityGroup = self.get_node_from_destination_affinityGroup(filename)
        if node_destination_affinityGroup:
            file_homenode = self.get_file_homenode(dict(node_destination_affinityGroup[0]))
            if not file_homenode:
                return HttpResponse(status=500)
            else:
                ip = file_homenode['IP']
                port = file_homenode['port']
                values = {'file_name' : filename}
                url = self.http + str(ip) + ":"+ str(port) + self.path_save_file
                files = {'file_obj': request.data['file_obj']}
                try:
                    # import pdb; pdb.set_trace()
                    result = requests.post(url ,files=files , data =values)
                except Exception as e:
                    print(e)
                    return HttpResponse(status = 500)
                else:
                    if result.status_code == 201:
                        return HttpResponse(status = 201)
                    else:
                        return HttpResponse(status = result.status_code)
        return HttpResponse(status = 500)

class DownloadFile(APIView,FileUtility):

    path_save_file = "/admin/webapp/save-file"
    path_get_file_touple = "/admin/webapp/get-file/"
    def get(self,request):
        filename = self.request.query_params.get('fileName','')
        node_destination_affinityGroup = self.get_node_from_destination_affinityGroup(filename)
        if node_destination_affinityGroup:
            # get the home node which contains the file.
            ip = dict(node_destination_affinityGroup[0])['IP']
            port = dict(node_destination_affinityGroup[0])['port']
            try:
                file_home_node = requests.get(self.http + ip + ":"+ port + self.path_get_file_touple +"?fileName="+ filename)
                file_home_node = file_home_node.json()
            except Exception as e:
                print(e)
                return HttpResponse(status = 500)

            if not file_home_node:
                return HttpResponse(status=404)
            else:
                # import pdb; pdb.set_trace()
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
                        return HttpResponse(status = 200)
                    else:
                        return HttpResponse(status = result.status_code)
        return HttpResponse(status = 500)


