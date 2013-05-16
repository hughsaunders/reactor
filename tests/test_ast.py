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

import unittest2
import reactor.ast


class AstTests(unittest2.TestCase):
    def setUp(self):
        self.node1 = {'strfield': 'testing',
                      'intfield': 3,
                      'arrayfield': [1, 2, 3]}

    def tearDown(self):
        pass

    def _eval(self, node, expression):
        ast = reactor.ast.FilterBuilder(reactor.ast.FilterTokenizer(),
                                        expression).build()
        return ast.eval_node(node)

    def test_int_equality(self):
        self.assertTrue(self._eval(self.node1, 'intfield = 3'))
        self.assertFalse(self._eval(self.node1, 'intfield = 2'))

    def test_int_comparison(self):
        self.assertTrue(self._eval(self.node1, 'intfield > 2'))
        self.assertTrue(self._eval(self.node1, 'intfield < 4'))
        self.assertFalse(self._eval(self.node1, 'intfield > 4'))
        self.assertFalse(self._eval(self.node1, 'intfield < 2'))
