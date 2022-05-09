#!/usr/bin/python3.8

import requests
from io import StringIO
from requests.auth import HTTPBasicAuth
import json
import re
import os
from collections import OrderedDict
from pprint import pformat
import datetime
from time import sleep

uid = os.environ.get('uid')
pwd = os.environ.get('pwd')
tid = os.environ.get('tid')
urs = os.environ.get('urs')

def app_trigger(data):
    alertid = data['alert']['alertId']
    alertlink = data['alert']['permalink']
    aid = int((data['alert']['permalink'])[46:52])
    ### get account group name from account group ID ###
    url = 'https://api.thousandeyes.com/v6/account-groups.json/?aid={0}'.format(aid)
    headers = {'Content-Type': 'application/json'}
    auth = HTTPBasicAuth(uid,pwd)
    account_grps = ((requests.request('GET',url,headers=headers,auth=auth)).json())['accountGroups']
    account = [d['accountGroupName'] for d in account_grps if d['aid'] == aid][0]
    ### get alert agents, testId, and path roundId ###
    testid_roundid_kvd = {}
    alert_det_url = 'https://api.thousandeyes.com/v7/alerts/end-to-end-server/{0}/?aid={1}'.format(alertid,aid)
    alert_det = requests.request('GET',alert_det_url,headers=headers,auth=auth).json()
    testid = alert_det['testId']
    testid_det_url = 'https://api.thousandeyes.com/v6/net/path-vis/{0}.json/?aid={1}'.format(testid,aid)
    testid_det = requests.request('GET',testid_det_url,headers=headers,auth=auth).json()
    roundid = testid_det['net']['pathVis'][0]['roundId']
    agents = [d['agentId'] for d in alert_det['agents']]
    testid_roundid_kvd[testid] = roundid
    ### for each alert agent and test, get the trace ###
    dataset = ''
    for agent in agents:
        for k,v in testid_roundid_kvd.items():
            sleep(1)
            path_route_url = 'https://api.thousandeyes.com/v6/net/path-vis/{0}/{1}/{2}.json/?aid={3}'.format(k,agent,v,aid)
            path_route_det = (requests.request('GET',path_route_url,headers=headers,auth=auth).json())
            try:
                agentname = path_route_det['net']['pathVis'][0]['agentName']
            except:
                agentname = path_route_det['net']['pathVis']
            testname = path_route_det['net']['test']['testName']
            try:
                route_trace = path_route_det['net']['pathVis'][0]['routes'][0]['hops'][-1]
            except:
                if len(path_route_det['net']['pathVis']) != 0:
                    route_trace = path_route_det['net']['pathVis']['hops'][-1]
            if (len(agentname) != 0 and len(route_trace) != 0):
                head = '\n#### destination: '+testname+' from agent: '+agentname+\
                        ' ####\n#### forward trace packet loss towards destination at node: ####\n'
                hop_data = re.sub(r",|'|{|}","",(pformat(route_trace)))
                hopset = head + hop_data
                dataset = dataset + '\n' + hopset
    pldata = str('#### Account group: {0} - Alert ID: {1} ####\n#### Alert Link: {2}'.format(account,alertid,alertlink) + dataset)
    slackdata = {"text": pldata}
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    r = requests.post(urs, json=slackdata, headers=headers)
    response = str(r.status_code) + ' ' + r.text
    return response

def lambda_handler(event, context):
    '''Forward default network alert rule alert data to uddos_te_alert_trace'''
    data = json.loads(event['body'])
    #data = event ## use with lambda test json
    if data['eventType'] == 'WEBHOOK_TEST':
        appmsg = 'te_alert_trace app trigger test: {0}'.format(data)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Appmsg ": appmsg
            })
        }
        #logging.getLogger('Lambda UDDOS ThousandEyes Agents path loss data').info\
        ('#### WEBHOOK_TEST ####\n#### data: {0}'.format(data))
    elif data['eventType'] == 'ALERT_NOTIFICATION_TRIGGER':
        response = app_trigger(data)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "slack post  ": response
            })
        }
    elif data['eventType'] == 'ALERT_NOTIFICATION_CLEAR':
        return {"statusCode": 200}
