from celery import Celery
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.decorators import task
from .models import Misc
from .models import AffinityGroupView
from .models import Filetuple
from .models import Contact
from django.db.models import Min
from .serializers import AffinityGroupViewSerializer
import requests
import yaml
import time
from math import log2
import json

# Fetch gossip paramaters
with open('webapp/gossip.yaml', 'r') as file:
    configs = yaml.load(file, Loader=yaml.FullLoader)

my_ip = requests.get('https://api.ipify.org').text


def node_with_min_rtt(visited):
    """
    Finds member with minimum round-trip-time from the
    membership list for the purpose of selecting gossip targets
    """
    nodes = AffinityGroupView.objects.order_by('rtt')
    for node in nodes:
        if node.IP not in visited and node.IP != my_ip:
            return node
    return None



def update_heartbeat():
    """
    Updates heartbeat for the responsible entities such as
    its own tuple in the membership list and stored files indices in filetuples
    """
    my_mem_list = AffinityGroupView.objects.filter(IP=my_ip)
    if my_mem_list:
        my_mem_list = my_mem_list[0]
        my_mem_list.heartbeatCount = Misc.objects.get(name='heartbeat').count
        my_mem_list.timestamp = Misc.objects.get(name='heartbeat').count
        my_mem_list.save()
        my_filetuples = Filetuple.objects.filter(IP=my_ip)
        for filetuple in my_filetuples:
            filetuple.heartbeatCount = Misc.objects.get(name='heartbeat').count
            filetuple.timestamp = Misc.objects.get(name='heartbeat').count
            filetuple.save()




def update_contact_heartbeat():
    """
    If active contact, updates heartbeat for its contact tuple in
    Contact membership list
    """
    my_contact = Contact.objects.filter(IP=my_ip)
    if my_contact:
        hbt = Misc.objects.get(name='heartbeat').count
        my_contact[0].heartbeatCount = hbt
        my_contact[0].timestamp = hbt
        my_contact[0].save()




def construct_payload(data, TTL):
    """
    Builds a payload for disseminating membership lists [Group View, Contacts, Filetuples]
    within the affinity group
    """
    payload = {}
    if not data:
        payload['nodes'] = [entry for entry in AffinityGroupView.objects.all().values()]
        payload['contacts'] = [entry for entry in Contact.objects.all().values()]
        payload['filetuples'] = [entry for entry in Filetuple.objects.all().values()]
    else:
        payload = data
        hbt = Misc.objects.get(name='heartbeat').count
        for node in payload['nodes']:
            if node["IP"] == my_ip:
                node['heartbeatCount'] = hbt
        for contact in payload['contacts']:
            if contact["IP"] == my_ip:
                contact['heartbeatCount'] = hbt
        for filetuple in payload['filetuples']:
            if filetuple["IP"] == my_ip:
                filetuple['heartbeatCount'] = hbt
    payload['TTL'] = TTL
    return payload




@periodic_task(run_every=configs['GOSSIP_PERIOD'], name="disseminate_heartbeat", ignore_result=True)
def disseminate_heartbeat(TTL=2, data={}):
    """
    Runs every gossip period, updates its heartbeat and gossips the
    membership lists to target nodes(fan-out)
    """
    TTL = int(TTL)
    if TTL > 0:
        fan_out = configs['FAN_OUT']
        visited = []
        update_heartbeat()
        payload = construct_payload(data, TTL)
        _iter = 0
        exception = False
        while _iter < fan_out and AffinityGroupView.objects.all().count():
            node = node_with_min_rtt(visited)
            if node == None:
                break            
            t1 = time.time()
            try:
                res = requests.post('http://' + node.IP + ':' + node.port + '/heartbeat', json.dumps(payload))
            # TODO: catch requests.exceptions.OSError,Timeout,ConnectionError
            except Exception as e:
                print(e)
                exception = True
            if not exception:
                exception = False
                t2 = time.time()
                node.rtt = max(node.rtt, t2 - t1)
                node.save()
            visited.append(node.IP)
            _iter = _iter + 1




@periodic_task(run_every=configs['GOSSIP_PERIOD'], name="disseminate_contact_heartbeat", ignore_result=True)
def disseminate_contact_heartbeat():
    """
    Runs every gossip period only if node is active contact and
    gossips its contact list after updating the heartbeat
    """
    if len(Contact.objects.filter(actual=True)):
        update_contact_heartbeat()
        payload = {}
        exception = False
        contacts = Contact.objects.all()
        payload['contacts'] = [entry for entry in contacts.values()]
        
        for contact in contacts: 
            t1 = time.time()
            try:
                res = requests.post('http://' + contact.IP + ':' + contact.port + '/contact-heartbeat', json.dumps(payload))
            # TODO: catch requests.exceptions.OSError,Timeout,ConnectionError
            except Exception as e:
                print(e)
                exception = True
            if not exception:
                exception = False
                t2 = time.time()
                contact.rtt = max(contact.rtt, t2 - t1)
                contact.save()

        


@periodic_task(run_every=configs['T_FAIL']/2, name="detect_failure", ignore_result=True)
def detect_failure():
    """
    Runs every half of T_fail time and checks the hearbeat updates.
    Raise failure if heartbeat not update for 2 * T_fail time and
    intimate other members in the group about this failure
    """
    mem_list = AffinityGroupView.objects.all()    
    nodes = []
    now = Misc.objects.get(name='heartbeat').count
    for member in mem_list:
        if now - member.timestamp > (2 * configs['T_FAIL']):
            if member.IP not in nodes:
                nodes.append(member.IP)
        elif now - member.timestamp > configs['T_FAIL']:
            member.isFailed = True
            member.save()

    contacts = []
    my_group = Misc.objects.get(name='heartbeat').groupID
    contact_list = Contact.objects.all()  
    now = Misc.objects.get(name='heartbeat').count
    for contact in contact_list:
        if now - contact.timestamp > (2 * configs['T_FAIL']):
            if contact.IP not in contacts:
                contacts.append(contact.IP)
        elif now - contact.timestamp > configs['T_FAIL']:
            contact.isFailed = True
            contact.save()

    if nodes or contacts:
        payload = {}
        payload['nodes'] = nodes
        payload['contacts'] = contacts
        for member in mem_list:
            if member.IP not in nodes:
                try:
                    res = requests.post('http://' + member.IP + ':' + member.port + '/delete-node', json.dumps(payload))
                # TODO: catch requests.exceptions.OSError,Timeout,ConnectionError
                except Exception as e:
                    print(e)
    


@periodic_task(run_every=1.0, name="increment_heartbeat", ignore_result=True)
def increment_heartbeat():
    """
    Runs every second and increment heartbeat for this node
    """
    counter = Misc.objects.select_for_update().get_or_create(name='heartbeat')[0]
    counter.count += 1
    counter.save()
