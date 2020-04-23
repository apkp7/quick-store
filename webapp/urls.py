from django.urls import path,include
from rest_framework import routers
from . import views
from . import gossip
from . import node

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
    path('heartbeat', gossip.listen_heartbeat),
    path('delete-node', gossip.delete_node),
    path('contact-heartbeat', gossip.intergroup_hearbeat),
    path('admin/webapp/check_node',node.check_node),
    path('admin/webapp/add_first_node',node.add_first_node),
    path('admin/webapp/add_node',node.add_node),
    path('admin/webapp/update_groupid',node.update_groupId_in_misc),
]
