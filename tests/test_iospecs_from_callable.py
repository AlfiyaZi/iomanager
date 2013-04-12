import pytest
import unittest
from iomanager import (
    IOProcessor,
    AnyType,
    iospecs_from_callable,
    combine_iospecs,
    )

class ResultTest(object):
    """ Confirm that the result dictionary is compatible with the
        'IOProcessor.verify' method parameters. """
    def test_result(self):
        result = iospecs_from_callable(self.callable)
        
        # Construct dummy iovals. For each key in 'required', 'optional', set
        # that key value to 'None' in the dummy ioval.
        iovals = {}
        for item in result.itervalues():
            for ikey in item:
                iovals.setdefault(ikey, None)
        
        IOProcessor(**result).verify(iovals)

class IOSpecValueTest(unittest.TestCase):
    def iospec_value_test(self, iospec_name, expected_list):
        result = iospecs_from_callable(self.callable)
        expected = {ikey: AnyType for ikey in expected_list}
        assert result[iospec_name] == expected
    

class TestParametersEmpty(IOSpecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj():
            pass
        return callable_obj
    
    def test_required_iospec(self):
        self.iospec_value_test('required', [])
    
    def test_optional_iospec(self):
        self.iospec_value_test('optional', [])

class TestParametersRequired(IOSpecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(a):
            pass
        return callable_obj
    
    def test_required_iospec(self):
        self.iospec_value_test('required', ['a'])
    
    def test_optional_iospec(self):
        self.iospec_value_test('optional', [])

class TestParametersOptional(IOSpecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(b=None):
            pass
        return callable_obj
    
    def test_required_iospec(self):
        self.iospec_value_test('required', [])
    
    def test_optional_iospec(self):
        self.iospec_value_test('optional', ['b'])

class TestParametersBothRequiredAndOptional(IOSpecValueTest, ResultTest):
    @property
    def callable(self):
        def callable_obj(a, b=None):
            pass
        return callable_obj
    
    def test_required_iospec(self):
        self.iospec_value_test('required', ['a'])
    
    def test_optional_iospec(self):
        self.iospec_value_test('optional', ['b'])

@pytest.mark.a
class TestNonFunctionCallable(unittest.TestCase):
    def callable_test(
        self,
        callable_class,
        required_keys=[],
        optional_keys=[],
        ):
        callable_obj = callable_class()
        
        result = iospecs_from_callable(callable_obj)
        
        assert result == {
            'required': {ikey: AnyType for ikey in required_keys},
            'optional': {ikey: AnyType for ikey in optional_keys},
            }
    
    def test_no_parameters(self):
        class Custom(object):
            def __call__(self):
                pass
        
        self.callable_test(Custom)
    
    def test_required(self):
        class Custom(object):
            def __call__(self, a):
                pass
        
        self.callable_test(Custom, ['a'], [])
    
    def test_optional(self):
        class Custom(object):
            def __call__(self, b=None):
                pass
        
        self.callable_test(Custom, [], ['b'])
    
    def test_required_and_optional(self):
        class Custom(object):
            def __call__(self, a, b=None):
                pass
        self.callable_test(Custom, ['a'], ['b'])
    
    def test_self_has_default(self):
        """ This should never happen, but in case it does, we have it
            covered. """
        class Custom(object):
            def __call__(self=None, b=None):
                pass
        self.callable_test(Custom, [], ['b'])
    
    def test_non_callable_object(self):
        with pytest.raises(TypeError):
            iospecs_from_callable(object())







