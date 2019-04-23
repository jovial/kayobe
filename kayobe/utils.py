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

import base64
import glob
import logging
import os
import six
import subprocess
import sys

import yaml


LOG = logging.getLogger(__name__)

_SHARE_PATH = os.path.join(sys.prefix, "share", "kayobe")
_BIN_PATH = os.path.join(sys.prefix, "bin")


def get_data_files_path(*relative_path):
    """Given a relative path to a data file, return the absolute path"""
    # Detect editable pip install / python setup.py develop and use a path
    # relative to the source directory
    src_path = resolve_egg_link('kayobe')
    if src_path:
        return os.path.join(src_path, *relative_path)
    return os.path.join(_SHARE_PATH, *relative_path)


def resolve_egg_link(package):
    egg_glob = os.path.join(
        sys.prefix, 'lib*', 'python*', '*-packages', '%s.egg-link' % package
    )
    egg_link = glob.glob(egg_glob)
    if egg_link:
        with open(egg_link[0], "r") as f:
            return f.readline().strip()


def yum_install(packages):
    """Install a list of packages via Yum."""
    cmd = ["sudo", "yum", "-y", "install"]
    cmd += packages
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        print("Failed to install packages %s via Yum: returncode %d" %
              (", ".join(packages), e.returncode))
        sys.exit(e.returncode)


def galaxy_install(role_file, roles_path, force=False):
    """Install Ansible roles via Ansible Galaxy."""
    cmd = ["ansible-galaxy", "install"]
    cmd += ["--roles-path", roles_path]
    cmd += ["--role-file", role_file]
    if force:
        cmd += ["--force"]
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        LOG.error("Failed to install Ansible roles from %s via Ansible "
                  "Galaxy: returncode %d", role_file, e.returncode)
        sys.exit(e.returncode)


def galaxy_remove(roles_to_remove, roles_path):
    """Remove Ansible roles via Ansible Galaxy."""
    cmd = ["ansible-galaxy", "remove"]
    cmd += ["--roles-path", roles_path]
    cmd += roles_to_remove
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        LOG.error("Failed to remove Ansible roles %s via Ansible "
                  "Galaxy: returncode %d",
                  ",".join(roles_to_remove), e.returncode)
        sys.exit(e.returncode)


def read_file(path, mode="r"):
    """Read the content of a file."""
    with open(path, mode) as f:
        return f.read()


def read_yaml_file(path):
    """Read and decode a YAML file."""
    try:
        content = read_file(path)
    except IOError as e:
        print("Failed to open config dump file %s: %s" %
              (path, repr(e)))
        sys.exit(1)
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        print("Failed to decode config dump YAML file %s: %s" %
              (path, repr(e)))
        sys.exit(1)


def is_readable_dir(path):
    """Check whether a path references a readable directory."""
    if not os.path.exists(path):
        return {"result": False, "message": "Path does not exist"}
    if not os.path.isdir(path):
        return {"result": False, "message": "Path is not a directory"}
    if not os.access(path, os.R_OK):
        return {"result": False, "message": "Directory is not readable"}
    return {"result": True}


def is_readable_file(path):
    """Check whether a path references a readable file."""
    if not os.path.exists(path):
        return {"result": False, "message": "Path does not exist"}
    if not os.path.isfile(path):
        return {"result": False, "message": "Path is not a file"}
    if not os.access(path, os.R_OK):
        return {"result": False, "message": "File is not readable"}
    return {"result": True}


def run_command(cmd, quiet=False, check_output=False, **kwargs):
    """Run a command, checking the output.

    :param quiet: Redirect output to /dev/null
    :param check_output: Whether to return the output of the command
    :returns: The output of the command if check_output is true
    """
    if isinstance(cmd, six.string_types):
        cmd_string = cmd
    else:
        cmd_string = " ".join(cmd)
    LOG.debug("Running command: %s", cmd_string)
    if quiet:
        with open("/dev/null", "w") as devnull:
            kwargs["stdout"] = devnull
            kwargs["stderr"] = devnull
            subprocess.check_call(cmd, **kwargs)
    elif check_output:
        return subprocess.check_output(cmd, **kwargs)
    else:
        subprocess.check_call(cmd, **kwargs)


def quote_and_escape(value):
    """Quote and escape a string.

    Adds enclosing single quotes to the string passed, and escapes single
    quotes within the string using backslashes. This is useful for passing
    'extra vars' to Ansible. Without this, Ansible only uses the part of the
    string up to the first whitespace.

    :param value: the string to quote and escape.
    :returns: the quoted and escaped string.
    """
    if not isinstance(value, six.string_types):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def escape_jinja(string):
    """Escapes a string so that jinja template variables are not expanded

    :param string: the string to escape
    :return: the escaped string
    """
    # We base64 encode the string to avoid the need to escape characters.
    # This is because ansible has some parsing quirks that makes it fairly
    # hard to escape stuff in generic way.
    # See: https://github.com/ansible/ansible/issues/10464

    b64_value = base64.b64encode(string.encode())
    return ''.join(('{{', "'", b64_value.decode(), "' | b64decode ", '}}'))


def setup_env():
    """If the environmental variable: KAYOBE_DISABLE_ENV_AUTODETECT is not
    set, this will attempt to detect the location of kayobe-config from the
    egg-link and source the environment setup script (kayobe-env).

    Does not return.

    """

    if "KAYOBE_DISABLE_ENV_AUTODETECT" not in os.environ:
        env_path = resolve_egg_link('kayobe-config')
        if not env_path:
            env_path = "/etc/kayobe"
        env_path = os.path.join(env_path, "kayobe-env")
        script_path = resolve_egg_link('kayobe')
        if script_path:
            script_path = os.path.join(script_path, "bin")
        else:
            script_path = _BIN_PATH
        script_path = os.path.join(script_path, "kayobe-env-helper")
        os.execvp(script_path, [script_path, env_path] + sys.argv)
