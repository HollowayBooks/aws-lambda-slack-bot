# Copyright 2019 Holloway Inc


class CommandException(Exception):
  """
  Exception of which message will be just reported as slack response
  (i.e. without showing the stacktrace as well)
  """
  pass


def hello():
  """
  Prints hello world
  """
  return "Hello world!"


# Map of commands to the actual function that implements them
COMMANDS = {
  'hello': hello,
}


def helpcmd(cmd=None) -> str:
  """
  Function to print help messages, which are just docstring on each
  command function
  """
  if cmd:
    try:
      return COMMANDS[cmd].__doc__
    except KeyError:
      return "command *{}* does not exist".format(cmd)
  else:
    return "Available commands: {}\nType:\n/bot <command> help\nFor info about each command".format(", ".join(
      COMMANDS.keys()))