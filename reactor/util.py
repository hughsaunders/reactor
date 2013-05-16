#!/usr/bin/env python
#
# Copyright 2013 Rackspace US, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# some simple utilites for wrapping, unwrapping, and otherwise
# managing messages
#

import socket


MY_HOSTNAME = None


def message_wrap(message, name, source_type,
                 source_opts=None,
                 default_ttl=5):
    global MY_HOSTNAME

    if source_opts is None:
        source_opts = {}

    if MY_HOSTNAME is None:
        MY_HOSTNAME = socket.gethostname()

    header = {'source': name,
              'source_type': source_type,
              'source_opts': source_opts,
              'hostname': MY_HOSTNAME}

    if not 'message' in message:
        message = {'message': message,
                   'headers': []}

    ttl = default_ttl

    if len(message['headers']) > 0:
        ttl = int(message['headers'][-1].get('ttl', default_ttl)) - 1

    header['ttl'] = ttl

    message['headers'].append(header)
    return message


def message_strip(message):
    if not 'message' in message:
        raise ParameterError('not a wrapped message')

    return message['message']
