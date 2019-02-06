# AWS Lambda Slack bot

This repository contains some minimal but useful scaffolding to create a Slack bot
deployed on AWS Lambda.

# Why?

If you want to build a simple Slack bot, [AWS Lambda](https://aws.amazon.com/lambda/) is an
ideal platform to use, because it has little to no management overhead.
Plus you want something that is easy to change and operate, because you want to spend most
of your time on your applications rather than tooling.

We didn’t see a project that handled all the pieces needed, so this scaffolding shows the
basic ways to tie together the APIs and AWS services in a simple way you can extend or
enhance.

Goals:

- Use AWS Lambda and [SAM](https://github.com/awslabs/serverless-application-model) to manage
  deployment in an easy but extensible way
- Make it easy to send messages to Slack from any app (like using
  [AWS SNS](https://aws.amazon.com/sns/))
- Make it easy to implement new commands on the bot

**This code is not heavily tested but has been useful internally at Holloway, so we’re
sharing it in case it’s useful.**

# Architecture

The app is composed in two parts, inbound and outbound:

**Inbound** receives Slack commands via a webhook and enqueues them in an SQS queue, from
there another Lambda parses and executes them.
Many commands can be easily added in the file `commands.py`, just like a Python function.

**Outbound** instead subscribes to any SNS topic, retrieves messages and publishes them on
any Slack channel configured via routing rules.
A topic will be created automatically but many other can be just added on `template.yml`.

# Deploy

This repository uses [SAM](https://github.com/awslabs/serverless-application-model) to deploy
the code.

# Extend

To extend you can either add new commands your bot can run or add more SNS Topic it will
be listening to.
The logic is just Python code, so new commands and features can be added easily.

## Add a command

To add a new command, create a new function on the file `commands.py` like this:

```python
def helloname(person: str):
  """
  Says hello to anybody, usage: /bot helloname <name>
  """
  return "Hello {}".format(person)
```

Then add it to the `COMMANDS` dictionary at the bottom of the file, the key will be the command
name:

```python
COMMANDS = { 'hello': hello, 'hellon': helloname}
```

That’s it. If you want to add more complex function, typical things you may need are new
AWS permissions, and you can add them on `template.yml`, or new python libraries that you can add on `Pipfile`

## Add a routing rule

A routing rule is used by the outbound component to route SNS messages to the Slack
channel of your choice, to add a new rule you can just add it to the array present in the
file `outbound.py`:

```python
SLACK_ROUTING_RULES = [
  SlackRoutingRule('*', '*', '#general'),
]
```

By default everything is sent to the channel `#general`, for example let’s suppose we want to send
messages with Subject that contains `alerts` to the `#alerts` channel, we can do this:

```python
SLACK_ROUTING_RULES = [
  SlackRoutingRule('*', '*alerts*', '#alerts'),
  SlackRoutingRule('*', '*', '#general'),
]
```

Keep in mind that the first rule that matches will be executed and the others discarded,
so keep the broader/catchall one at the end of the array.

The syntax is: `SlackRoutingRule('<topic-arn-pattern>', '<subject-pattern>', '<slack-channel-name>')`
. The pattern follows the rules of the shell `glob` matching, in particular the
[fnmatch](https://docs.python.org/2/library/fnmatch.html) library is used.

## Listen to other topics

New SNS topics to listen to can be added on `template.yml`, in particular in the `OutboundFunction` part, for example:

```yaml
OutboundFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: ./deliverable.zip
    Handler: outbound.lambda_handler
    Runtime: python3.6
    Events:
      BotNofications:
        Type: SNS
        Properties:
          Topic: { Ref: OutboundTopic }
      # New Topic
      OtherTopicNotifications:
        Type: SNS
        Properties:
          Topic: <your-topic-arn-goes-here>
```

# TODO

- [ ] Improve deploy instructions
- [ ] Improve Slack messages formatting
- [ ] Add Slack buttons support, e.g.
      to rerun the same command
