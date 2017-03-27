import yaml
import requests
import json
import uuid
import itertools
import config

RESULTSDB_API_URL = config.resultdb_api_url
TRUSTED_CA = 'ca.crt'

#read dva tests results
with open(config.yaml, 'r') as f:
    doc = yaml.load(f)

#initialize list of unique amis
amis = []
for ele in doc:
    amis.append(ele['ami'])
amis = list(set(amis))

results = []

for ami in amis:
    tests = []
    for ele in doc:
        if ele['ami'] == ami:
            if 'test' in ele:
                test = []
                test.append(ele['ami'])
                test.append(ele['test']['name'])
                test.append(ele['test']['result'])
                tests.append(test)
    results.append(tests)

def get_error_from_request(request):
    try:
        return request.json().get('message')
    except ValueError:
        return request.text

def create_result(testcase, outcome, ref_url, data, groups=None):
    if not groups:
        groups = []
    post_req = requests.post(
        '{0}/results'.format(RESULTSDB_API_URL),
        data=json.dumps({
            'testcase': testcase,
            'groups': groups,
            'outcome': outcome,
            'ref_url': ref_url,
            'data': data}),
        headers={'content-type': 'application/json'},
        verify=TRUSTED_CA)
    if post_req.status_code == 201:
        return True
    else:
        message = get_error_from_request(post_req)
        raise RuntimeError(message)

for ami_result in results:
    #assign unique group id to each ami
    group_uuid = str(uuid.uuid4())
    overall_outcome = 'passed'
    ami_id = ''
    #iterate through all test cases for an ami
    for result in ami_result:
        ami_id = result[0]
        testcase = 'dva.ami.{0}'.format(result[1])
        outcome = result[2]
        if outcome == 'failed' or outcome == 'skip':
            overall_outcome = 'FAILED'
        if outcome == 'skip':
            outcome = 'NEEDS_INSPECTION'
        ref_url = 'http://some.jenkins.url/'
        # Additional information
        data = {
            'item': result[0]
        }

        #create an entry for a test case into resultdb
        create_result(testcase, outcome, ref_url, data, groups=[group_uuid])

    #create an entry for overall outcome for an ami into resultdb
    create_result('dva.ami', overall_outcome, 'http://some.jenkins.url/', {'item': ami_id}, groups=[group_uuid])

