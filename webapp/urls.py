from django.urls import path,include
from rest_framework import routers
from . import views
from .models import AffinityGroupView, Contact, Filetuple, Counter, File
# from . import gossip, tasks


router =  routers.DefaultRouter()
router.register('AffinityGroupView',views.AffinityGroupViewEndpoint)
router.register('Contact',views.ContactEndpoint)
router.register('Filetuple',views.FiletupleEndpoint)
urlpatterns = [
    path('',include(router.urls)),
    path('admin/webapp/search-node/',views.SearchNode.as_view()),
    path('admin/webapp/upload/',views.UploadFile.as_view()),
    path('admin/webapp/save-file/',views.SaveFile.as_view()),
    path('admin/webapp/download',views.DownloadFile.as_view()),
    path('admin/webapp/get-file/',views.GetFiletuple.as_view()),
    path('admin/webapp/get-affinity-group/',views.GetAffinityGroup.as_view()),
    path('admin/webapp/ping/',views.Ping.as_view()),
    # path('heartbeat', gossip.listen_heartbeat),
]
