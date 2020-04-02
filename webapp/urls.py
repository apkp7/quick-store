from django.urls import path,include
from rest_framework import routers
from . import views, gossip, tasks


router =  routers.DefaultRouter()
router.register('AffinityGroupView',views.AffinityGroupViewEndpoint)
router.register('Contact',views.ContactEndpoint)
router.register('Filetuple',views.FiletupleEndpoint)
urlpatterns = [
    path('',include(router.urls)),
    path('admin/webapp/search-node/',views.SearchNode.as_view()),
    path('admin/webapp/insert-file/',views.InsertFile.as_view()),
    path('heartbeat', gossip.listen_heartbeat),
]
