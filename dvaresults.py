import argparse
import os
import yaml
import json


def parse_results(dva_yaml):
    # Read dva tests results
    with open(dva_yaml, 'r') as f:
        doc = yaml.load(f)
    #  If run from jenkins, BUILD_URL should be available
    ref_url = os.environ.get('BUILD_URL')
    res = {}
    body = {}
    msg = {}
    results = {}
    # iterate over each testcase
    for item in doc:
        if 'test' in item:
            name = 'dva.ami.' + item['test']['name']
            outcome = item['test']['result'].upper()
            if outcome == 'SKIP':
                outcome = 'NEEDS_INSPECTION'
            results[name] = {}
            data = {}
            data.update(item=item['ami'])
            results[name].update(data=data)
            results[name].update(outcome=outcome)
            results[name].update(ref_url=ref_url)
            results[name].update(note=None)
            testcase = {}
            testcase.update(name=name)
            testcase.update(ref_url=ref_url)
            results[name].update(testcase=testcase)
    msg.update(results=results)
    msg.update(ref_url=ref_url)
    body.update(msg=msg)
    res.update(body=body)
    json_data = json.dumps(res)
    return json_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Imports dva results into resultsdb')
    parser.add_argument('dva_yaml', help='Path to dva results yaml')
    args = parser.parse_args()

    results = parse_results(args.dva_yaml)
