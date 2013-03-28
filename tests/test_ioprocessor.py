""" Copyright (c) 2013 Josh Matthias <python.ioprocess@gmail.com> """

import datetime
import dateutil
import decimal
import pytest
import string
import uuid
import unittest

import ioprocess
from ioprocess import IOProcessor
from ioprocess.ioprocess import (
    IOProcessFailureError,
    TypeCheckSuccessError,
    TypeCheckFailureError,
    )

_NotSet = object()

# ---------------------- Dictionary keys checking ----------------------

class ProcessTest(unittest.TestCase):
    class CustomType(object):
        pass
    
    class InvalidType(object):
        pass
    
    def good_iovals_test(self, iovals):
        IOProcessor().process(iovals, **self.trial_tspecs())
    
    def bad_iovals_test(self, iovals):
        with pytest.raises(IOProcessFailureError):
            self.good_iovals_test(iovals)
    
    def trial_tspecs(self):
        return dict(
            optional={},
            required={},
            unlimited=False,
            )

class BasicTspecTest(ProcessTest):
    @classmethod
    def required_iovals(cls):
        return dict(a=0, b=1, c=2)
    
    @classmethod
    def optional_iovals(cls):
        return dict(d=3, e=4, f=5)
    
    @classmethod
    def required_tspec(cls):
        return {'a': int, 'b': int, 'c': int}
    
    @classmethod
    def optional_tspec(cls):
        return {'d': int, 'e': int, 'f': int}
    
    @classmethod
    def all_iovals(cls):
        result = cls.required_iovals()
        result.update(cls.optional_iovals())
        return result

class TestRequiredTspec(BasicTspecTest):
    def trial_tspecs(self):
        return dict(
            required=self.required_tspec()
            )
    
    def test_good_iovals(self):
        self.good_iovals_test(self.required_iovals())
    
    def test_missing_ioval_raises(self):
        iovals = self.required_iovals()
        del iovals['c']
        self.bad_iovals_test(iovals)
    
    def test_extra_ioval_raises(self):
        iovals = self.required_iovals()
        iovals['x'] = 9
        self.bad_iovals_test(iovals)

class TestOptionalTspec(BasicTspecTest):
    def trial_tspecs(self):
        return dict(optional=self.optional_tspec())
    
    def test_good_iovals(self):
        self.good_iovals_test(self.optional_iovals())
    
    def test_missing_ioval_passes(self):
        iovals = self.optional_iovals()
        del iovals['f']
        self.good_iovals_test(iovals)
    
    def test_extra_ioval_raises(self):
        iovals = self.optional_iovals()
        iovals['x'] = 9
        self.bad_iovals_test(iovals)

class TestUnlimitedIOVals(BasicTspecTest):
    def trial_tspecs(self):
        return dict(unlimited=True)
    
    def test_empty_iovals_passes(self):
        self.good_iovals_test(iovals={})
    
    def test_many_iovals_passes(self):
        keys = list(string.ascii_lowercase)
        iovals = dict(zip(keys, range(len(keys))))
        self.good_iovals_test(iovals)

class TestRequiredAndOptionalBoth(BasicTspecTest):
    def trial_tspecs(self):
        return dict(
            required=self.required_tspec(),
            optional=self.optional_tspec(),
            )
    
    def test_all_iovals_pass(self):
        self.good_iovals_test(iovals=self.all_iovals())
    
    def test_missing_required_raises(self):
        iovals = self.all_iovals()
        del iovals['a']
        self.bad_iovals_test(iovals)
    
    def test_missing_optional_passes(self):
        iovals = self.all_iovals()
        del iovals['d']
        self.good_iovals_test(iovals)
    
    def test_extra_kwarg_raises(self):
        iovals = self.all_iovals()
        iovals['x'] = 9
        self.bad_iovals_test(iovals)



# ------------------------- ListOf tspec tests -------------------------

class TestListOf(ProcessTest):
    def trial_tspecs(self):
        return dict(
            required={
                'a': ioprocess.ListOf(int)
            }
        )
    
    def test_empty_list_passes(self):
        self.good_iovals_test({'a': list()})
    
    def test_invalid_type_raises(self):
        self.bad_iovals_test({'a': self.InvalidType()})
    
    def test_none_type_raises(self):
        self.bad_iovals_test({'a': None})
    
    def test_length_one_passes(self):
        self.good_iovals_test({'a': [0]})
    
    def test_item_none_value_raises(self):
        self.bad_iovals_test({'a': [None,]})
    
    def test_all_bad_type_raises(self):
        self.bad_iovals_test({'a': ['a', 'b', 'c']})
    
    def test_one_bad_type_raises(self):
        self.bad_iovals_test({'a': [0, 1, 'a']})

class ListOfStructuredTest(object):
    def listof_tspec(self):
        return {
            'a': ioprocess.ListOf(
                    {'a': int,}
                )
            }
    
    def trial_tspecs(self):
        return {
            self.tspec_parameter_qualifier: self.listof_tspec()
        }
    
    def good_item(self, n=0):
        return {'a': n}
    
    def good_iovals(self, n=1):
        result ={
            'a': [self.good_item(n) for n in range(n)],
            }
        return result
    
    def test_good_list_passes(self):
        self.good_iovals_test(self.good_iovals())
    
    def test_empty_list_passes(self):
        self.good_iovals_test({'a': []})
    
    def test_none_raises(self):
        self.bad_iovals_test({'a': [None,]})
    
    def test_extra_key_raises(self):
        iovals = self.good_iovals()
        iovals['a'][0]['x'] = 1
        self.bad_iovals_test(iovals)
    
    def test_one_bad_value_raises(self):
        iovals = self.good_iovals()
        iovals['a'].append({'b': 1})
        self.bad_iovals_test(iovals)

class TestListOfStructuredOptional(ListOfStructuredTest, ProcessTest):
    tspec_parameter_qualifier = 'optional'

class TestListOfStructuredRequired(ListOfStructuredTest, ProcessTest):
    tspec_parameter_qualifier = 'required'
    
    def test_missing_key_passes(self):
        iovals = self.good_iovals()
        del iovals['a'][0]['a']
        self.bad_iovals_test(iovals)

class ListOfStructuredNestedTest(object):
    def listof_tspec(self):
        return {
            'a':  ioprocess.ListOf(
                {
                    'a': {
                        'b': int
                    }
                }
            )
        }
    
    def trial_tspecs(self):
        return {
            self.tspec_parameter_qualifier: self.listof_tspec()
        }
    
    def good_item(self, n=0):
        return {'a': {'b': n}}
    
    def good_iovals(self, n=1):
        result ={
            'a': [self.good_item(n) for n in range(n)],
            }
        return result
    
    def test_good_list_passes(self):
        self.good_iovals_test(self.good_iovals())
    
    def test_extra_nested_key_raises(self):
        iovals = self.good_iovals()
        iovals['a'][0]['a']['x'] = 2
        self.bad_iovals_test(iovals)

class TestListOfStructuredNestedOptional(ListOfStructuredNestedTest, ProcessTest):
    tspec_parameter_qualifier = 'optional'

class TestListOfStructuredNestedRequired(ListOfStructuredNestedTest, ProcessTest):
    tspec_parameter_qualifier = 'required'
    
    def test_missing_nested_key_raises(self):
        iovals = self.good_iovals()
        del iovals['a'][0]['a']['b']
        self.bad_iovals_test(iovals)

class TestListOfNestedListOf(ProcessTest):
    def trial_tspecs(self):
        return dict(
            required={
                'a': ioprocess.ListOf(
                    ioprocess.ListOf(int)
                )
            }
        )
    
    def good_iovals(self, x=3, y=3):
        return {
            'a': [range(y) for i in range(x)]
        }
    
    def test_good_iovals_passes(self):
        self.good_iovals_test(self.good_iovals())
    
    def test_empty_nested_list_passes(self):
        self.good_iovals_test(
            {'a': [[]]}
        )
    
    def test_one_wrong_type_raises(self):
        self.bad_iovals_test(
            {'a': ['a']}
        )
    
    def test_one_wrong_nested_type_raises(self):
        self.bad_iovals_test(
            {'a': [[1, 2, 'a']]}
        )



# ----------------------- Structured tspec tests -----------------------

class StructuredTest(ProcessTest):
    """ 'Structured' means that the tspec dictionary includes values that are
        nested tspec dictionaries. """
    @classmethod
    def structured_iovals(cls):
        return {
            'i': 0,
            'j': 1,
            'a': {'b': 2, 'c': 3},
            'w': {'x': 4, 'y': {'z': 5}},
            }
    
    @classmethod
    def structured_tspec(cls):
        return {
            'i': int,
            'j': int,
            'a': {'b': int, 'c': int},
            'w': {'x': int, 'y': {'z': int}}
            }
    
    def none_value_raises_test(self):
        iovals = self.structured_iovals()
        iovals['a'] = None
        self.bad_iovals_test(iovals)

class TestStructuredRequired(StructuredTest):
    def trial_tspecs(self):
        return dict(
            required=self.structured_tspec()
            )
    
    def test_ok_iovals(self):
        self.good_iovals_test(self.structured_iovals())
    
    def test_none_value_raises(self):
        self.none_value_raises_test()
    
    def test_missing_structured_ioval_raises(self):
        iovals = self.structured_iovals()
        del iovals['a']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_ioval_raises(self):
        iovals = self.structured_iovals()
        del iovals['a']['b']
        self.bad_iovals_test(iovals)
    
    def test_extra_nested_ioval_raises(self):
        iovals = self.structured_iovals()
        iovals['a']['xxx'] = 9
        self.bad_iovals_test(iovals)

class TestStructuredOptional(StructuredTest):
    def trial_tspecs(self):
        return dict(
            optional=self.structured_tspec()
            )
    
    def test_ok_iovals(self):
        self.good_iovals_test(self.structured_iovals())
    
    def test_none_value_raises(self):
        self.none_value_raises_test()
    
    def test_empty_iovals_passes(self):
        self.good_iovals_test(iovals={})
    
    def test_missing_structured_ioval_passes(self):
        iovals = self.structured_iovals()
        del iovals['a']
        self.good_iovals_test(iovals)
    
    def test_missing_nested_ioval_passes(self):
        iovals = self.structured_iovals()
        del iovals['a']['b']
        self.good_iovals_test(iovals)
    
    def test_extra_nested_ioval_raises(self):
        iovals = self.structured_iovals()
        iovals['a']['xxx'] = 9
        self.bad_iovals_test(iovals)

class TestStructuredRequiredEmpty(ProcessTest):
    def trial_tspecs(self):
        return dict(
            required={'a': {}}
            )
    
    def test_ok_iovals_passes(self):
        self.good_iovals_test({'a': {}})
    
    def test_missing_structured_ioval_raises(self):
        self.bad_iovals_test({})
    
    def test_extra_nested_ioval_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredOptionalEmpty(ProcessTest):
    def trial_tspecs(self):
        return dict(
            optional={'a': {}}
            )
    
    def test_ok_iovals_passes(self):
        self.good_iovals_test({'a': {}})
    
    def test_missing_structured_ioval_passes(self):
        self.good_iovals_test({})
    
    def test_extra_nested_ioval_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredUnlimited(ProcessTest):
    """ When 'unlimited' is True, only top-level keyword arguments are
        unlimited. Structured data should still be checked for unknown keyword
        arguments. """
    
    def trial_tspecs(self):
        return dict(
            optional={'a': {'b': int}},
            unlimited=True
            )
    
    def test_extra_kwarg_passes(self):
        self.good_iovals_test({'x': 1})
    
    def test_extra_nested_kwarg_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredRequiredOverridesOptional(ProcessTest):
    """ When structured tspec keys appear in both the 'required' and the
        'optional' tspecs, the 'required' condition should take precedence. """
    @classmethod
    def required_tspec(cls):
        return {
            'a': int,
            'b': {'x': int, 'y': int},
            'c': {
                'q': {'m': int},
                'r': {'n': int},
                },
            }
    
    @classmethod
    def optional_tspec(cls):
        return {
            'a': int,
            'b': {'y': int, 'z': int},
            'c': {
                'r': {'n': int},
                's': {'o': int},
                },
            }
    
    def all_iovals(self):
        return dict(
            a=1,
            b=dict(x=2, y=3, z=4,),
            c=dict(
                q=dict(m=5),
                r=dict(n=6),
                s=dict(o=7),
                ),
            )
    
    def trial_tspecs(self):
        return dict(
            required=self.required_tspec(),
            optional=self.optional_tspec(),
            )
    
    def test_all_iovals_passes(self):
        self.good_iovals_test(self.all_iovals())
    
    def test_missing_nested_optional_passes(self):
        iovals = self.all_iovals()
        del iovals['b']['z']
        self.good_iovals_test(iovals)
    
    def test_missing_nested_structured_optional_passes(self):
        iovals = self.all_iovals()
        del iovals['c']['s']
        self.good_iovals_test(iovals)
    
    def test_missing_required_overlap_raises(self):
        iovals = self.all_iovals()
        del iovals['a']
        self.bad_iovals_test(iovals)
    
    def test_missing_structured_required_overlap_raises(self):
        iovals = self.all_iovals()
        del iovals['b']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_required_raises(self):
        iovals = self.all_iovals()
        del iovals['b']['x']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_required_overlap_raises(self):
        iovals = self.all_iovals()
        del iovals['b']['y']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_structured_required_raises(self):
        iovals = self.all_iovals()
        del iovals['c']['q']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_structured_required_overlap_raises(self):
        iovals = self.all_iovals()
        del iovals['c']['r']
        self.bad_iovals_test(iovals)



# ------------------------ Type checking tests -------------------------

@pytest.mark.typecheck
class TypeCheckingTest(unittest.TestCase):
    """ Confirm that coercion behaves correctly when the tspec 'type object' is
        a 'class' object. """
    
    class CustomType(object):
        """ A custom type for testing type-checking. """
    
    class CustomSubclassType(CustomType):
        """ A custom type for testing type-checking. """
    
    class InvalidType(object):
        """ A custom type for testing type-checking. """

class TestTypeCheckingBasic(TypeCheckingTest):
    def get_process_result(
        self,
        value,
        tspec_kind='required',
        expected_type=None
        ):
        if expected_type is None:
            expected_type = self.CustomType
        
        ioprocessor = IOProcessor()
        ioprocessor.process(
            iovals={'a': value},
            **{tspec_kind: {'a': expected_type}}
            )
    
    def process_passes_test(self, *pargs, **kwargs):
        self.get_process_result(*pargs, **kwargs)
    
    def process_raises_test(self, *pargs, **kwargs):
        with pytest.raises(IOProcessFailureError):
            self.process_passes_test(*pargs, **kwargs)
    
    def test_invalid_type_raises_required(self):
        self.process_raises_test(self.InvalidType(), 'required')
    
    def test_invalid_type_raises_optional(self):
        self.process_raises_test(self.InvalidType(), 'optional')
    
    def test_none_value_passes(self):
        self.process_passes_test(None)
    
    def test_correct_type_passes(self):
        self.process_passes_test(self.CustomType())
    
    def test_correct_type_passes_subclass(self):
        """ Confirm that an instance of a subclass of the specified type passes
            coercion.
            
            In order to change this behavior to reject subclasses, the user
            should use the 'type_checking_functions' attribute. """
        self.process_passes_test(self.CustomSubclassType())
    
    def test_anytype_accepts_anything(self):
        """ The 'AnyType' type should accept values of any type. """
        class ArbitraryType(object):
            """ An arbitrary value type. """
        
        arbitrary_value = ArbitraryType()
        self.process_passes_test(
            value=ArbitraryType(),
            expected_type=ioprocess.AnyType,
            )

class TypeCheckingExtendedTest(object):
    def call_process_method(self, value):
        ioprocessor = IOProcessor()
        
        iovals = {
            'a': self.make_extended_ioval(value)
            }
        
        required = {
            'a': self.make_extended_tspec()
            }
        
        ioprocessor.process(
            iovals=iovals,
            required=required
            )
    
    def test_correct_type_passes(self):
        self.call_process_method(self.CustomType())
    
    def test_invalid_type_raises(self):
        with pytest.raises(IOProcessFailureError):
            self.call_process_method(self.InvalidType())

class TestTypeCheckingStructured(TypeCheckingTest, TypeCheckingExtendedTest):
    """ Confirm that type checking is occurring when the tspec 'type object' is
        a dictionary. """
    
    def make_extended_ioval(self, value):
        return {'b': value}
    
    def make_extended_tspec(self):
        return {'b': self.CustomType}

class TestTypeCheckingListOf(TypeCheckingTest, TypeCheckingExtendedTest):
    """ Confirm that type checking is occurring when the tspec 'type object' is
        a ListOf instance. """
    
    def make_extended_ioval(self, value):
        return [value]
    
    def make_extended_tspec(self):
        return ioprocess.ListOf(self.CustomType)

class TestTypeCheckingCustomFunction(TypeCheckingTest):
    """ Confirm type checking behavior when custom type-checking functions are
        in use. """
    def get_process_result(self, value, custom_function):
        ioprocessor = IOProcessor(
            type_checking_functions={self.CustomType: custom_function}
            )
        ioprocessor.process(
            iovals={'a': self.CustomType()},
            required={'a': self.CustomType}
            )
    
    def process_passes_test(self, *pargs):
        self.get_process_result(*pargs)
    
    def process_raises_test(self, *pargs):
        with pytest.raises(IOProcessFailureError):
            self.process_passes_test(*pargs)
    
    def test_type_check_failure_error(self):
        """ When a custom type-checking function raises a TypeCheckFailureError,
            type checking fails even if the value would have passed type
            checking normally.
            
            This can be used for 'subclass rejection'. For example: 'int' type
            rejects 'bool' values. """
        def reject_value(value):
            raise TypeCheckFailureError
        self.process_raises_test(self.CustomType(), reject_value)
    
    def test_type_check_success_error(self):
        """ When a custom type-checking function raises a TypeCheckSuccessError,
            type checking passes even if the value would have been rejected
            normally. """
        def accept_value(value):
            raise TypeCheckSuccessError
        self.process_passes_test(self.InvalidType(), accept_value)
    
@pytest.mark.typecheck
class TestTypeCheckingDefaultFunctions(unittest.TestCase):   
    """ Confirm that default type checking functions behave as expected. """ 
    def default_function_passes_test(self, value, expected_type):
        type_checking_function = (
            ioprocess.default_type_checking_functions[expected_type]
            )
        type_checking_function(value)
    
    def default_function_raises_test(self, *pargs):
        with pytest.raises(IOProcessFailureError):
            self.default_function_passes_test(*pargs)
    
    def test_int_gets_int_passes(self):
        self.default_function_passes_test(123, int)
    
    def test_decimal_gets_decimal_passes(self):
        self.default_function_passes_test(
            decimal.Decimal('1.23'),
            decimal.Decimal,
            )
    
    def test_int_gets_bool_fails(self):
        bool_value = True
        self.default_function_raises_test(bool_value, int)
    
    def test_decimal_gets_bool_fails(self):
        bool_value = True
        self.default_function_raises_test(bool_value, decimal.Decimal)



# ------------------------ Type coercion tests -------------------------

def retrieve_location(location_tuple, container):
    if not isinstance(location_tuple, tuple):
        location_tuple = (location_tuple,)
    
    this_index = location_tuple[0]
    remainder = location_tuple[1:]
    
    if isinstance(container, ioprocess.ListOf):
        target_value = container.tspec_obj
    else:
        target_value = container[this_index]
    
    if not remainder:
        return target_value
    
    return retrieve_location(remainder, target_value)

@pytest.mark.coercion
class TypeCoercionTest(unittest.TestCase):
    def get_coercion_result(self, tspecs=None, iovals=None):
        coercion_functions = self.get_coercion_functions()
        ioprocessor = IOProcessor(
            coercion_functions=self.get_coercion_functions()
            )
        
        tspecs = tspecs or self.get_tspecs()
        iovals = iovals or self.get_iovals()
        
        return ioprocessor.process(iovals, **tspecs)
    
    def get_result_value(self, location, **kwargs):
        result_dict = self.get_coercion_result(**kwargs)
        
        result_value = retrieve_location(location, result_dict)
        
        return result_value
    
    def type_test(self, location, expected_type, **kwargs):
        result_value = self.get_result_value(location, **kwargs)
        assert isinstance(result_value, expected_type)
    
    def value_test(self, location, expected_value, **kwargs):
        result_value = self.get_result_value(location, **kwargs)
        assert result_value == expected_value

class TypeCoercionProcessTest(TypeCoercionTest):
    """ A test to confirm that calling IOProcessor.process() uses the coercion
        functions (provided by the 'coercion_functions' argument) correctly. """
    
    class BeforeCoercionType(object):
        """ A type that can be coerced to YesCoercionType. """
    
    class YesCoercionType(object):
        """ A coercion function is assigned to this type. """
    
    class NoCoercionType(object):
        """ No coercion function is assigned to this type. """
    
    def coerce_yescoerciontype(self, ioval):
        if isinstance(ioval, self.BeforeCoercionType):
            return self.YesCoercionType()
        
        return ioval
    
    def get_coercion_functions(self):
        
        return {
            self.YesCoercionType: self.coerce_yescoerciontype,
        }

class TestTypeCoercionArguments(TypeCoercionProcessTest):
    """ Confirm coercion for each of 'required', 'optional', and
        'unlimited' arguments. """
    
    def get_iovals(self):
        return {'a': self.BeforeCoercionType()}
    
    def make_tspecs(self, tspec_kind, **kwargs):
        result = {
            tspec_kind: {
                'a': self.YesCoercionType
                }
            }
        result.update(kwargs)
        return result
    
    def coercion_test(self, tspecs):
        self.type_test('a', self.YesCoercionType, tspecs=tspecs)
    
    def coercion_argument_test(self, tspec_kind):
        tspecs = self.make_tspecs(tspec_kind)
        
        self.coercion_test(tspecs)
    
    def test_coercion_required(self):
        self.coercion_argument_test('required')
    
    def test_coercion_optional(self):
        self.coercion_argument_test('optional')
    
    def test_coercion_required_unlimited(self):
        """ Coercion occurs when 'unlimited' is used with 'required'. """
        tspecs = self.make_tspecs('required', unlimited=True)
        self.coercion_test(tspecs)
    
    def test_coercion_optional_unlimited(self):
        """ Coercion occurs when 'unlimited' is used with 'optional'. """
        tspecs = self.make_tspecs('optional', unlimited=True)
        self.coercion_test(tspecs)

class TestTypeCoercionRequiredOverridesOptional(TypeCoercionProcessTest):
    """ Confirm that when 'required' and 'optional' are both
        present, 'required' overrides 'optional. """
    
    def get_tspecs(self):
        return {
            'required': {'a': self.YesCoercionType},
            'optional': {'a': self.NoCoercionType},
            }
    
    def get_iovals(self):
        return {'a': self.BeforeCoercionType()}
    
    def test_coercion(self):
        self.type_test('a', self.YesCoercionType)

class TestTypeCoercionOther(TypeCoercionTest):
    """ Test type coercion situations not covered by other tests. """
    
    def get_coercion_functions(self):
        """ For this test case, no coercion functions are assigned. """
        return {}
    
    def coercion_test(self, type_obj, iovalue, expected):
        tspecs = {
            'required': {'a': type_obj}
            }
        iovals = {'a': iovalue}
        
        result = self.get_result_value('a', tspecs=tspecs, iovals=iovals)
        
        assert result == expected
    
    def test_list_preserved_through_coercion(self):
        """ When a list is provided as an argument value, its length and order
            are preserved.
            
            It is important that 'trial_list' is not in a 'natural sorted'
            order. Otherwise, the coercion function wouldn't need to preserve
            the input order; it would only need to sort the result, and it could
            get lucky. """
        trial_list = list(u'aWMp8CAjRjMd039Hy1o4fLCv0RsVZxTB')
        expected = list(trial_list)
        
        type_obj = ioprocess.ListOf(unicode)
        self.coercion_test(type_obj, trial_list, expected)

@pytest.mark.coercion
class TypeCoercionDefaultFunctionsTest(unittest.TestCase):
    """ Confirm that the default type coercion functions behave as expected. """
    class ArbitraryType(object):
        """ This class is used to test a coercion function's effect upon an
            arbitrarily-typed value. """
    
    def coercion_test(self, type_obj, iovalue, expected):
        coercion_function = self.coercion_functions[type_obj]
        
        result = coercion_function(iovalue)
        assert result == expected
    
    def arbitrary_value_test(self, type_obj):
        class ArbitraryType(object):
            """ An arbitrary type which should pass through coercion
                unchanged. """
        arbitrary_value = self.ArbitraryType()
        self.coercion_test(type_obj, arbitrary_value, arbitrary_value)

class TestTypeCoercionDefaultFunctionsInput(TypeCoercionDefaultFunctionsTest):
    """ Confirm that input values coerce correctly. """
    coercion_functions = ioprocess.ioprocess.default_coercion_functions_input
    
    # ------------- Arbitrary types pass with no coercion --------------
    
    def test_unicode_gets_arbitrary_type(self):
        self.arbitrary_value_test(unicode)
    
    def test_datetime_gets_arbitrary_type(self):
        self.arbitrary_value_test(datetime.datetime)
    
    def test_uuid_gets_arbitrary_type(self):
        self.arbitrary_value_test(uuid.UUID)
    
    def test_decimal_gets_arbitrary_type(self):
        self.arbitrary_value_test(decimal.Decimal)
    
    # --------------------- Coercion result tests ----------------------
    
    def test_unicode_gets_str(self):
        unicode_value = u'abc'
        str_value = str(unicode_value)
        self.coercion_test(unicode, str_value, unicode_value)
    
    def test_datetime_gets_string(self):
        """ An ISO-formatted datetime string coerces to a datetime value. """
        dt_value = datetime.datetime.utcnow()
        dt_string = dt_value.isoformat()
        self.coercion_test(
            datetime.datetime,
            iovalue=dt_string,
            expected=dt_value,
            )
    
    #def test_dtdate_gets_string(self):
    #    pass
    
    def test_uuid_gets_string(self):
        uuid_value = uuid.uuid4()
        uuid_string = str(uuid_value)
        self.coercion_test(
            uuid.UUID,
            iovalue=uuid_string,
            expected=uuid_value,
            )
    
    def test_decimal_gets_int(self):
        int_value = 123
        decimal_value = decimal.Decimal(int_value)
        self.coercion_test(decimal.Decimal, int_value, decimal_value)

class TestTypeCoercionDefaultFunctionsOutput(TypeCoercionDefaultFunctionsTest):
    """ Confirm that values coerce correctly on output.
        
        On output, some value types are coerced to string values by default.
        This is done with JSON-serialization in mind. """
    coercion_functions = ioprocess.ioprocess.default_coercion_functions_output
    
    # ------------- Arbitrary types pass with no coercion --------------
    
    def test_datetime_gets_arbitrary_type(self):
        self.arbitrary_value_test(datetime.datetime)
    
    def test_uuid_gets_arbitrary_type(self):
        self.arbitrary_value_test(uuid.UUID)
    
    # --------------------- Coercion result tests ----------------------
    
    def test_datetime_to_string(self):
        """ 'datetime' values should coerce to ISO-8601-formatted strings. """
        dt_value = datetime.datetime.utcnow()
        dt_string = dt_value.isoformat()
        self.coercion_test(
            datetime.datetime,
            iovalue=dt_value,
            expected=dt_string,
            )
    
    #def test_dtdate_to_string(self):
    #    """ 'DTDate' values should coerce to pure-date ISO-8601-formatted
    #        strings, based on the 'application universal date start time'.
    #        For now, that is UTC - 8:00. """
    #        pass
    
    def test_uuid_to_string(self):
        """ UUID values coerce to strings on output. """
        uuid_value = uuid.uuid4()
        uuid_string = str(uuid_value)
        self.coercion_test(
            uuid.UUID,
            iovalue=uuid_value,
            expected=uuid_string,
            )

@pytest.mark.coercion
class TestTypeCoercionCycle(unittest.TestCase):
    """ Confirm that certain types are preserved through the coercion 'cycle'.
        
        When these types are coerced to output, then coerced back to input, the
        result is equal to the starting value. """
    
    def coercion_cycle_test(self, type_obj, starting_value):
        output_processor = ioprocess.output_processor()
        input_processor = ioprocess.input_processor()
        
        tspec =  {'value': type_obj}
        
        output_result = output_processor.process(
            iovals={'value': starting_value},
            required=tspec,
            )
        
        final_result = input_processor.process(
            iovals=output_result,
            required=tspec,
            )
        
        final_value = final_result['value']
        
        assert final_value == starting_value
    
    def test_datetime(self):
        dt_value = datetime.datetime.utcnow()
        self.coercion_cycle_test(datetime.datetime, dt_value)
    
    #def test_dtdate(self):
    #    pass
    
    def test_uuid(self):
        uuid_value = uuid.uuid4()
        self.coercion_cycle_test(uuid.UUID, uuid_value)







