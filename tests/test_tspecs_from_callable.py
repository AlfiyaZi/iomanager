import pytest
import unittest
from ioprocess import (
    IOProcessor,
    AnyType,
    tspecs_from_callable,
    combine_tspecs,
    )

class ResultTest(object):
    """ Confirm that the result dictionary is compatible with the
        'IOProcessor.verify' method parameters. """
    def test_result(self):
        result = tspecs_from_callable(self.callable)
        
        # Construct dummy iovals. For each key in 'required', 'optional', set
        # that key value to 'None' in the dummy ioval.
        iovals = {}
        for item in result.itervalues():
            for ikey in item:
                iovals.setdefault(ikey, None)
        
        IOProcessor().verify(iovals, **result)

class TspecValueTest(unittest.TestCase):
    def tspec_value_test(self, tspec_name, expected_list):
        result = tspecs_from_callable(self.callable)
        expected = {ikey: AnyType for ikey in expected_list}
        assert result[tspec_name] == expected
    

class TestParametersEmpty(TspecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj():
            pass
        return callable_obj
    
    def test_required_tspec(self):
        self.tspec_value_test('required', [])
    
    def test_optional_tspec(self):
        self.tspec_value_test('optional', [])

class TestParametersRequired(TspecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(a):
            pass
        return callable_obj
    
    def test_required_tspec(self):
        self.tspec_value_test('required', ['a'])
    
    def test_optional_tspec(self):
        self.tspec_value_test('optional', [])

class TestParametersOptional(TspecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(b=None):
            pass
        return callable_obj
    
    def test_required_tspec(self):
        self.tspec_value_test('required', [])
    
    def test_optional_tspec(self):
        self.tspec_value_test('optional', ['b'])

class TestParametersBothRequiredAndOptional(TspecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(a, b=None):
            pass
        return callable_obj
    
    def test_required_tspec(self):
        self.tspec_value_test('required', ['a'])
    
    def test_optional_tspec(self):
        self.tspec_value_test('optional', ['b'])







