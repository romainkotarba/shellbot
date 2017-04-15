# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys
import yaml
import importlib

sys.path.insert(0, os.path.abspath('..'))

class ShellMessage(object):
    def __init__(self, message, markdown=None, file=None):
        self.message = message
        self.markdown = markdown
        self.file = file

class Shell(object):
    """
    Parses input and reacts accordingly
    """

    def __init__(self, context, mouth=None, inbox=None):
        self.context = context
        self.mouth = mouth
        self.inbox = inbox

        self._commands = {}
        self.load_commands(context.get('shell.commands', []))

        self.line=None
        self.count=0
        self.verb = None

    def configure(self, settings):
        """
        Changes settings of the shell

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``shell`` and below, and update
        the context accordingly.

        >>>shell.configure({'shell': {
               'commands':
                  ['examples.exception.state', 'examples.exception.next']
               }})

        This can also be written in a more compact form::

        >>>shell.configure({'shell.commands':
               ['examples.exception.state', 'examples.exception.next']
               })

        Note that this function does preserve commands that could have been
        loaded previously.
        """

        self.context.parse(settings, 'shell', 'commands', default=[])

        self.load_default_commands()
        self.load_commands(self.context.get('shell.commands', []))

    @property
    def name(self):
        """
        Retrieves the dynamic name of this bot

        :return: The value of ``bot.name`` key in current context
        :rtype: str

        """
        return self.context.get('bot.name', 'Shelly')

    @property
    def version(self):
        """
        Retrieves the version of this bot

        :return: The value of ``bot.version`` key in current context
        :rtype: str

        """
        return self.context.get('bot.version', '*unknown*')

    def say(self, message, markdown=None, file=None):
        """
        Sends a response back from shell

        :param message: The message from the shell
        :type message: str or None

        :param markdown: A message using Markdown
        :type markdown: str or None

        :param file: path or URL to a file to attach
        :type file: str or None

        """
        if message in (None, ''):
            return

        if self.mouth:
            if markdown or file:
                self.mouth.put(ShellMessage(message, markdown, file))
            else:
                self.mouth.put(message)
        else:
            logging.info(str(message))

    @property
    def commands(self):
        """
        Lists available commands

        :return: a list of verbs
        :rtype: list of str

        This function provides with a dynamic inventory of all capabilities
        of this shell.

        Example:
        >>>print(shell.commands)
        ['*default', '*empty', 'help']
        """
        return sorted(self._commands.keys())

    def command(self, keyword):
        """
        Get one command

        :param keyword: the keyword for this command
        :type keyword: str

        :return: the instance for this command
        :rtype: command or None

        Example:
        >>>print(shell.command('help').information_message)
        Lists available commands and related usage information.

        """
        if keyword in self._commands.keys():
            return self._commands[keyword]
        return None

    def load_default_commands(self):
        """
        Loads default commands for this shell

        Example:
            >>>shell.load_default_commands()

        """
        labels = [
            'shellbot.commands.default',
            'shellbot.commands.echo',
            'shellbot.commands.empty',
            'shellbot.commands.help',
            'shellbot.commands.noop',
            'shellbot.commands.sleep',
            'shellbot.commands.version',
        ]
        self.load_commands(labels)

    def load_commands(self, commands=[]):
        """
        Loads commands for this shell

        :param commands: A list of commands to load
        :type commands: List of labels or list of commands

        Example:
            >>>commands = ['shellbot.commands.help']
            >>>shell.load_commands(commands)

        Each label should reference a python module that can be used
        as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.

        If objects are provided, they should duck type the command defined
        in ``base.py`` in ``shellbot.commands``.

        Example:
            >>>from shellbot.commands.version import Version
            >>>version = Version()
            >>>from shellbot.commands.help import Help
            >>>help = Help()
            >>>shell.load_commands([version, help])
        """
        for item in commands:
            self.load_command(item)

    def load_command(self, command):
        """
        Loads one command for this shell

        :param command: A command to load
        :type command: str or command

        If a string is provided, it should reference a python module that can
        be used as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.

        Example:
            >>>shell.load_command('shellbot.commands.help')

        If an object is provided, it should duck type the command defined
        in ``base.py`` in ``shellbot.commands``.

        Example:
            >>>from shellbot.commands.version import Version
            >>>command = Version()
            >>>shell.load_command(command)
        """
        if isinstance(command, str):
            try:
                module = importlib.import_module(command)
            except ImportError:
                (dummy, label) = command.split('.', 1)
                module = importlib.import_module(label)

            name = command.rsplit('.', 1)[1].capitalize()
            cls = getattr(module, name)
            command = cls(self)

        if command.keyword in self._commands.keys():
            logging.debug("Command '{}' has been replaced".format(
                command.keyword))

        command.context = self.context
        command.shell = self

        self._commands[ command.keyword ] = command

    def do(self, line):
        """
        Handles one line of text

        This function uses the first token as a verb, and looks for a command
        of the same name in the shell.

        If the command does not exist, the command ``*default`` is used
        instead. Default behavior is implemented in
        ``shellbot.commands.default`` yet you can load a different command
        for customization.

        If an empty line is provided, the command ``*empty`` is triggered.
        Default implementation is provided in ``shellbot.commands.empty``.

        """
        line = '' if line is None else unicode(line)  # sanity check
        logging.error(line)

        logging.debug(u"Handling: {}".format(line))
        self.line = line
        self.count += 1

        tokens = line.split(' ')
        verb = tokens.pop(0)
        if len(verb) < 1:
            verb = '*empty'

        if len(tokens) > 0:
            arguments = ' '.join(tokens)
        else:
            arguments = ''

        try:
            if verb in self._commands.keys():
                command = self._commands[verb]
                if command.is_interactive:
                    self.verb = verb
                    command.execute(arguments)
                else:
                    if not self.context.get('worker.busy', False):
                        self.say("Ok, working on it")
                    else:
                        self.say("Ok, will work on it as soon as possible")
                    self.inbox.put((command.keyword, arguments))

            elif '*default' in self._commands.keys():
                command = self._commands['*default']
                if command.is_interactive:
                    self.verb = verb
                    command.execute(arguments)
                else:
                    if not self.context.get('worker.busy', False):
                        self.say("Ok, working on it")
                    else:
                        self.say("Ok, will work on it as soon as possible")
                    self.inbox.put((verb, arguments))

            else:
                self.say(
                    u"Sorry, I do not know how to handle '{}'".format(verb))

        except Exception as feedback:
            self.say(
                u"Sorry, I do not know how to handle '{}'".format(verb))
            raise
