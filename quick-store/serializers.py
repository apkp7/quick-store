from rest_framework import serializers
from .models import AffinityGroupView,Contact,Filetuple, File

class AffinityGroupViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffinityGroupView
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class FiletupleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filetuple
        fields = '__all__'

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class FileDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['file_obj']