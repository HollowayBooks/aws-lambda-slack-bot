# Copyright 2019 Holloway Inc

from slackclient import SlackClient
import os
from typing import NamedTuple, Callable
from fnmatch import fnmatch
import yaml
import json

SC = SlackClient(os.environ['SLACK_TOKEN'])


class SlackRoutingRule(NamedTuple):
  """
  This class encapsulates a routing rule, used to identify
  which message should go to which Slack channel
  """

  # These two fields map SNS relative ones that hold
  # glob-style patterns that are used to identify if the
  # rule applies or not
  topicArn: str
  subject: str

  # This is the Slack channel name where we send the message
  channel: str

  # This field can be used if we want to replace the original Subject
  # while we send the message to Slack
  force_subject: str = None

  # This is a generic callback that can be used to transform the message
  # before sending it to Slack
  transform_message: Callable[[dict], None] = None


# List of routing rules, the first one that matches will be applied and the other ones
# skipped
SLACK_ROUTING_RULES = [
  SlackRoutingRule('*', '*', '#general'),
]

SLACK_MESSAGE_TEMPLATE = """
*{}*

```
{}
```
"""


def lambda_handler(event, context):
  """
  This function listens notifications coming from various SNS topics,
  matches them with a routing rule and notifies a particular Slack channel
  """
  for record in event['Records']:
    notification = record['Sns']
    print("Processing: " + json.dumps(notification, indent=2))
    topicArn = notification['TopicArn']
    message = notification['Message']
    parsed_message = json.loads(message)

    subject = notification['Subject']
    if not subject:
      subject = 'No subject'

    channel = None
    # We iterate over the rules and stop at the first match
    for rule in SLACK_ROUTING_RULES:
      if fnmatch(topicArn, rule.topicArn) and fnmatch(subject, rule.subject):
        print("Matched rule {}".format(repr(rule)))
        channel = rule.channel
        if rule.force_subject:
          subject = rule.force_subject
        if rule.transform_message:
          rule.transform_message(parsed_message)
        break

    message_yaml = yaml.dump(parsed_message, default_flow_style=False).strip()

    if channel:
      SC.api_call("chat.postMessage", channel=channel, text=SLACK_MESSAGE_TEMPLATE.format(subject, message_yaml))
      print("Sent message to Slack")
    else:
      print("No matching slack routing rule found")