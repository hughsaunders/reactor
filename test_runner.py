#!/usr/bin/env python


import unittest2
import sys


if __name__ == '__main__':
    loader = unittest2.TestLoader()
    tests = loader.discover('tests')
    testRunner = unittest2.runner.TextTestRunner(stream=sys.stdout,
                                                 verbosity=2)
    runner = testRunner.run(tests)
    sys.exit(not runner.wasSuccessful())
