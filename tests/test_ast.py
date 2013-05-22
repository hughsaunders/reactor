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

    def _eval(self, node, expression, ns=None):
        ast = reactor.ast.FilterBuilder(reactor.ast.FilterTokenizer(),
                                        input_expression=expression,
                                        ns=ns)
        return ast.eval_node(node)

    def test_int_equality(self):
        self.assertTrue(self._eval(self.node1, 'intfield = 3'))
        self.assertFalse(self._eval(self.node1, 'intfield = 2'))

        self.assertFalse(self._eval(self.node1, 'intfield != 3'))
        self.assertTrue(self._eval(self.node1, 'intfield != 2'))

    def test_int_comparison(self):
        self.assertTrue(self._eval(self.node1, 'intfield > 2'))
        self.assertTrue(self._eval(self.node1, 'intfield < 4'))
        self.assertFalse(self._eval(self.node1, 'intfield > 4'))
        self.assertFalse(self._eval(self.node1, 'intfield < 2'))

        self.assertFalse(self._eval(self.node1, 'intfield !> 2'))
        self.assertFalse(self._eval(self.node1, 'intfield !< 4'))
        self.assertTrue(self._eval(self.node1, 'intfield !> 4'))
        self.assertTrue(self._eval(self.node1, 'intfield !< 2'))

    def test_str_equality(self):
        self.assertTrue(self._eval(self.node1, 'strfield = "testing"'))
        self.assertFalse(self._eval(self.node1, 'strfield = "x"'))
        self.assertFalse(self._eval(self.node1, 'strfield != "testing"'))
        self.assertTrue(self._eval(self.node1, 'strfield != "x"'))

    def test_str_substring(self):
        self.assertTrue(self._eval(self.node1, '"test" in strfield'))
        self.assertFalse(self._eval(self.node1, '"x" in strfield'))

        self.assertFalse(self._eval(self.node1, '"test" !in strfield'))
        self.assertTrue(self._eval(self.node1, '"x" !in strfield'))

    # no array equality... no static arrays
    def test_len(self):
        self.assertTrue(self._eval(self.node1, 'count(arrayfield) = 3'))
        # Nones for invalid types
        self.assertEqual(self._eval(self.node1, 'count(intfield)'), None)

    def test_nth(self):
        self.assertTrue(self._eval(self.node1, 'nth(0,arrayfield) = 1'))
        self.assertFalse(self._eval(self.node1, 'nth(1,arrayfield) = 1'))
        self.assertEqual(self._eval(self.node1, 'nth(1,intfield)'), None)

    def test_str(self):
        self.assertTrue(self._eval(self.node1, 'str(intfield) = "3"'))
        self.assertTrue(self._eval(self.node1, 'str(0) = "0"'))

    def test_int(self):
        self.assertTrue(self._eval(self.node1, 'int(str(intfield)) = 3'))

    def test_min(self):
        self.assertTrue(self._eval(self.node1, 'min(arrayfield) = 1'))
        # this is odd
        self.assertFalse(self._eval(self.node1, 'min(intfield)'))

    def test_max(self):
        self.assertTrue(self._eval(self.node1, 'max(arrayfield) = 3'))
        # again with the odd.  Should it except on type?
        self.assertFalse(self._eval(self.node1, 'min(intfield)'))

    def test_count(self):
        self.assertTrue(self._eval(self.node1, 'count(arrayfield) = 3'))

    def test_union(self):
        self.assertTrue(self._eval(self.node1,
                                   'max(union(arrayfield, 4)) = 4'))
        self.assertTrue(self._eval(self.node1,
                                   'count(union(arrayfield, 4)) = 4'))

    def test_remove(self):
        self.assertTrue(self._eval(self.node1,
                                   'max(remove(arrayfield, 3)) = 2'))
        self.assertTrue(self._eval(self.node1,
                                   'count(remove(arrayfield, 3)) = 2'))

    def test_static_array(self):
        self.assertTrue(self._eval(self.node1,
                                   'arrayfield = [ 1, 2, 3 ]'))

    def test_ns(self):
        ns = {'foo': 'bar'}
        self.assertEqual(self._eval(self.node1, 'foo', ns), 'bar')

    def test_assignment(self):
        ns = {}
        self._eval(self.node1, 'arf := 3')

        self.assertEqual(ns['arf'], 3)
