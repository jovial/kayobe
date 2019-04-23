# Copyright (c) 2017 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
import os
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

from kayobe import version, utils
from kayobe.ansible import DEFAULT_CONFIG_PATH


class KayobeApp(App):

    def __init__(self):
        release_version = version.version_info.release_string()
        super(KayobeApp, self).__init__(
            description='Kayobe Command Line Interface (CLI)',
            version=release_version,
            command_manager=CommandManager('kayobe.cli'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    if "KAYOBE_DO_NOT_MODIFY_ENV_AUTODETECT" not in os.environ:
        path = utils.resolve_egg_link('kayobe-config')
        if not path:
            path = "/etc/kayobe"
        path = os.path.join(path, "kayobe-env")
        os.execvp("kayobe-env-helper", [
            sys.argv[0], path] + sys.argv[1:])
    myapp = KayobeApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
