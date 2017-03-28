import argparse
import os
import requests
import uuid
import yaml

RESULTSDB_APIS = {
    'prod': 'https://resultsdb.host.prod.eng.bos.redhat.com/api/v2.0',
    'stage': 'https://resultsdb.host.stage.eng.bos.redhat.com/api/v2.0',
    'dev': 'https://resultsdb-backend.host.dev.eng.pek2.redhat.com/api/v2.0',
}


def parse_results(dva_yaml):
    # Read dva tests results
    with open(dva_yaml, 'r') as f:
        doc = yaml.load(f)

    results = []
    for item in doc:
        if 'test' in item:
            results.append({
                'ami': item['ami'],
                'name': item['test']['name'],
                'result': item['test']['result'],
            })

    return results


def import_results(results, environment):
    # Assign unique group id for tests
    group_uuid = str(uuid.uuid1())

    url = '{0}/results'.format(RESULTSDB_APIS[environment])

    for result in results:
        testcase = 'dva.ami.{0}'.format(result['name'])
        outcome = result['result'].upper()
        if outcome == 'SKIP':
            outcome = 'NEEDS_INSPECTION'
        # If run from jenkins, BUILD_URL should be available
        ref_url = os.environ.get('BUILD_URL')

        # Create an entry for a test case into resultdb
        #headers = {'content-type': 'application/json'}
        body = {
            'testcase': testcase,
            'groups': [group_uuid],
            'outcome': outcome,
            'ref_url': ref_url,
            'data': {'item': result['ami']},
        }
        rsp = requests.post(url, json=body)

        if rsp.status_code != 201:
            try:
                error = rsp.json().get('message')
            except ValueError:
                error = rsp.text
            raise RuntimeError(error)


    return '{0}?groups={1}'.format(url, group_uuid)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Imports dva results into resultsdb')
    parser.add_argument('-e', '--environment',
                        default='dev',
                        choices=['prod', 'stage', 'dev'],
                        help='ResultsDB environment to use (prod, stage, dev)')
    parser.add_argument('dva_yaml', help='Path to dva results yaml')
    args = parser.parse_args()

    results = parse_results(args.dva_yaml)
    print(import_results(results, args.environment))
