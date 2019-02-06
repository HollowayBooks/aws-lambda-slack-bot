# Copyright 2019 Holloway Inc

import hmac
import functools
from time import time
import os
import hashlib
import boto3
from commands import COMMANDS, helpcmd
import json
from urllib.parse import parse_qs


def validate_slack_signature(fn):
  """
  Decorator used to validate Slack signature before executing the actual
  function
  """

  @functools.wraps(fn)
  def wrap(event, context):
    """Validate that the signature in the header matches the payload."""
    # This code was inspired by examples found online
    timestamp = event['headers']['X-Slack-Request-Timestamp']
    if abs(time() - int(timestamp)) > 60 * 5:
      return {"statusCode": 403, "body": "unauthorized"}

    signature = event['headers']['X-Slack-Signature']

    print("Calculating digest")
    req = str.encode('v0:' + str(timestamp) + ':') + event['body'].encode('utf-8')
    digest = 'v0=' + hmac.new(str.encode(os.environ['SLACK_SECRET']), req, hashlib.sha256).hexdigest()
    print("digest=%s signature=%s" % (digest, signature))
    if hmac.compare_digest(digest, signature):
      print("Valid signature")
      return fn(event, context)
    else:
      return {"statusCode": 403, "body": "unauthorized"}

  return wrap


@validate_slack_signature
def lambda_handler(event, context):
  """
  This function is called when Slack calls our API

  the logic here just enqueues the message in a SQS queue,
  for async processing. The reason is that Slack needs a
  very quick response otherwise it goes to timeout.
  """
  print(json.dumps(event))
  slack_message = parse_qs(event['body'])
  # {'token': ['...'],
  #  'team_id': ['your-team-id'],
  #  'team_domain': ['your-domain'],
  #  'channel_id': ['your-channel-id'],
  #  'channel_name': ['your-channel'],
  #  'user_id': ['sender-id'],
  #  'user_name': ['sender-username'],
  #  'command': ['/your-slash-command'],
  #  'text': ['message content'],
  #  'response_url': ['...'],
  #  'trigger_id': ['423341488807.173073584353.4442cfbe595731bcc332cf530ea82f82']}
  try:
    command, *args = slack_message['text'][0].split(" ")
    if command == 'help':
      return {"statusCode": 200, "body": helpcmd(*args)}
    elif command in COMMANDS:
      if len(args) > 0 and args[0] == 'help':
        return {"statusCode": 200, "body": helpcmd(command)}
      sqs = boto3.client('sqs')
      response = sqs.send_message(
        QueueUrl=os.environ['QUEUE_URL'],
        MessageBody=json.dumps({
          'slack_message': slack_message,
          'command': command,
          'args': args
        }))
      print(response)
      return {"statusCode": 200}
    else:
      return {"statusCode": 200, "body": "command {} does not exists!\n\n{}".format(command, helpcmd())}
  except Exception as ex:
    return {"statusCode": 200, "body": "Exception occurred: {}".format(ex)}