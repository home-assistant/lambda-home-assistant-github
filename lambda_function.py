from __future__ import print_function

import json

import config

VERBOSE = False


def lambda_handler(event, context, debug=False):
    if debug:
        import os
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dependencies'))
        print(os.path.join(os.path.dirname(__file__), 'dependencies'))

    from github3 import login

    if 'Records' in event:
        # SNS
        if VERBOSE:
            event_type = event['Records'][0]['Sns']['MessageAttributes']['X-Github-Event']['Value']
            print(event_type + ': ' + event['Records'][0]['Sns']['Message'])
        message = json.loads(event['Records'][0]['Sns']['Message'])
    else:
        # API
        message = event
        if VERBOSE:
            print('API: ' + json.dumps(event, indent=2))

    action = message.get('action')

    if 'pull_request' not in message or action != 'opened':
        print('Action: {}. Contains pull_request object: {}'.format(
            action, 'pull_request' in message))
        return

    pr_id = message['number']
    author = message['pull_request']['user']['login']

    target_repo_owner = message['pull_request']['base']['repo']['owner']['login']
    target_repo = message['pull_request']['base']['repo']['name']
    target_branch = message['pull_request']['base']['ref']

    if target_repo_owner != config.repo_owner or target_repo != config.repo:
        print("Got event for unexpected repo {}/{}".format(
            target_repo_owner, target_repo))
        return

    if target_branch != config.branch:
        print('PR is targetting {} branch, aborting'.format(target_branch))
        return

    if author in config.ignore_login:
        print('Ignoring pull requests from {}'.format(author))
        return

    if debug:
        print("DONE")
        return

    gh = login(config.user,
               password=config.token)

    issue = gh.issue(target_repo_owner, target_repo, pr_id)

    issue.create_comment(config.comment)

    print('Added comment to pull request {}'.format(pr_id))
