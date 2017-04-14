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

from base import Command

class Empty(Command):
    """
    Handles empty command
    """

    keyword = '*empty'
    information_message = 'Handles empty command.'
    is_hidden = True

    def execute(self, *args):
        """
        Handles empty command
        """
        if not hasattr(self, 'help_command'):
            self.help_command = self.shell.command('help')

        if self.help_command is None:
            raise Exception("No help command has been found")

        self.help_command.execute()