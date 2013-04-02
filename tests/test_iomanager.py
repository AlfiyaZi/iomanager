""" Copyright (c) 2013 Josh Matthias <python.iomanager@gmail.com> """

import datetime
import dateutil
import decimal
import pytest
import string
import uuid
import unittest

import iomanager
from iomanager import (
    IOProcessor,
    IOManager,
    VerificationFailureError,
    TypeCheckSuccessError,
    TypeCheckFailureError,
    )

_NotSet = object()

class Error(Exception):
    """ Base class for errors. """

class ConfirmationError(Error):
    """ Raised to confirm that a particular function or method has been
        called. """

class CustomType(object):
    """ A custom type used for testing type-checking. """

class CustomSubclassType(CustomType):
    """ A custom type used for testing type-checking. """

class CoercionTest(unittest.TestCase):
    class BeforeCoercionType(object):
        """ A type that coerces to YesCoercionType. """
    
    class YesCoercionType(object):
        """ A type with a custom coercion function. """
    
    def coerce_custom(self, value):
        if isinstance(value, self.BeforeCoercionType):
            return self.YesCoercionType()
        return value
    
    def setUp(self):
        self.ioprocessor = IOProcessor(
            coercion_functions={self.YesCoercionType: self.coerce_custom}
            )



# ------------------- Non-container 'iovalue' tests --------------------
    

class TestNonContainerVerifyTypeCheck(unittest.TestCase):
    def test_no_iospec_passes(self):
        IOProcessor().verify(
            iovalue=object()
            )
    
    def correct_type_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=object(),
            **{parameter_name: object}
            )
    
    def test_correct_type_passes_required(self):
        self.correct_type_passes_test('required')
    
    def test_correct_type_passes_optional(self):
        self.correct_type_passes_test('optional')
    
    def correct_type_subclass_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=CustomSubclassType(),
            **{parameter_name: CustomType}
            )
    
    def test_correct_type_subclass_passes_required(self):
        self.correct_type_subclass_passes_test('required')
    
    def test_correct_type_subclass_passes_optional(self):
        self.correct_type_subclass_passes_test('optional')
    
    def wrong_type_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            IOProcessor().verify(
                iovalue=object(),
                **{parameter_name: CustomType}
                )
    
    def test_wrong_type_raises_required(self):
        self.wrong_type_raises_test('required')
    
    def test_wrong_type_raises_optional(self):
        self.wrong_type_raises_test('optional')
    
    def none_value_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=None,
            **{parameter_name: object}
            )
    
    def test_none_value_passes_required(self):
        self.none_value_passes_test('required')
    
    def test_none_value_passes_optional(self):
        self.none_value_passes_test('optional')
    
    def anytype_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=object(),
            **{parameter_name: iomanager.AnyType}
            )
    
    def test_anytype_passes_required(self):
        self.anytype_passes_test('required')
    
    def test_anytype_passes_optional(self):
        self.anytype_passes_test('optional')
    
    def test_required_overrides_optional(self):
        IOProcessor().verify(
            iovalue=object(),
            required=object,
            optional=CustomType,
            )

@pytest.mark.a
class TestNonContainerVerifyTypeCheckCustomFunction(unittest.TestCase):
    """ Confirm type checking behavior when custom type-checking functions are
        in use. """
    def verify_test(self, value, custom_function):
        ioprocessor = IOProcessor(
            typecheck_functions={CustomType: custom_function}
            )
        ioprocessor.verify(
            iovalue=value,
            required=CustomType
            )
    
    def test_type_check_failure_error(self):
        """ When a custom type-checking function raises a TypeCheckFailureError,
            type checking fails even if the value would have passed type
            checking normally.
            
            This can be used for 'subclass rejection'. For example: 'int' type
            rejects 'bool' values. """
        def reject_value(value, expected_type):
            raise TypeCheckFailureError
        with pytest.raises(VerificationFailureError):
            self.verify_test(CustomType(), reject_value)
    
    def test_type_check_success_error(self):
        """ When a custom type-checking function raises a TypeCheckSuccessError,
            type checking passes even if the value would have been rejected
            normally. """
        def accept_value(value, expected_type):
            raise TypeCheckSuccessError
        self.verify_test(object(), accept_value)

class TestNonContainerVerifyStructure(unittest.TestCase):
    """ When dealing with non-container 'iospec' values, there is not much
        structure to-be-verified. This case only needs to test that 'unlimited'
        is ignored when non-container types are involved. """
    def unlimited_ignored_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            IOProcessor().verify(
                iovalue=object(),
                unlimited=True,
                **{parameter_name: CustomType}
                )
    
    def test_unlimited_ignored_required(self):
        self.unlimited_ignored_test('required')
    
    def test_unlimited_ignored_optional(self):
        self.unlimited_ignored_test('optional')

class TestNonContainerIOValueCoerce(CoercionTest):
    def test_no_iospec_passes(self):
        self.ioprocessor.coerce(
            iovalue=object()
            )
    
    def no_coercion_test(self, parameter_name):
        uncoerced_value = self.BeforeCoercionType()
        
        result = self.ioprocessor.coerce(
            iovalue=uncoerced_value,
            **{parameter_name: object}
            )
        
        assert result is uncoerced_value
    
    def test_no_coercion_required(self):
        self.no_coercion_test('required')
    
    def test_no_coercion_optional(self):
        self.no_coercion_test('optional')
    
    def yes_coercion_test(self, parameter_name):
        result = self.ioprocessor.coerce(
            iovalue=self.BeforeCoercionType(),
            **{parameter_name: self.YesCoercionType}
            )
        
        assert isinstance(result, self.YesCoercionType)
    
    def test_yes_coercion_required(self):
        self.yes_coercion_test('required')
    
    def test_yes_coercion_optional(self):
        self.yes_coercion_test('optional')
    
    def test_required_overrides_optional(self):
        uncoerced_value = self.BeforeCoercionType()
        
        result = self.ioprocessor.coerce(
            iovalue=uncoerced_value,
            required=object,
            optional=self.YesCoercionType,
            )
        
        assert result is uncoerced_value



# ---------------------- List-value IOSpec tests -----------------------

class TestIOSpecListVerify(unittest.TestCase):
    def setUp(self):
        self.ioprocessor = IOProcessor()
    
    def parameter_test(self, parameter_name, iovalue):
        self.ioprocessor.verify(
            iovalue=iovalue,
            **{parameter_name: [object]}
            )
    
    def good_iovalue_passes_test(self, parameter_name):
        self.parameter_test(parameter_name, [object()])
    
    def test_required_passes(self):
        self.good_iovalue_passes_test('required')
    
    def test_optional_passes(self):
        self.good_iovalue_passes_test('optional')
    
    def extra_item_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            self.parameter_test(parameter_name, [object(), object()])
    
    def test_extra_item_raises_required(self):
        self.extra_item_raises_test('required')
    
    def test_extra_item_raises_optional(self):
        self.extra_item_raises_test('optional')
    
    def missing_item_test(self, parameter_name):
        self.parameter_test(parameter_name, [])
    
    def test_missing_item_raises_required(self):
        with pytest.raises(VerificationFailureError):
            self.missing_item_test('required')
    
    def test_missing_item_passes_optional(self):
        self.missing_item_test('optional')
    
    def none_value_test(self, parameter_name):
        self.parameter_test(parameter_name, [None])
    
    def test_none_value_passes_required(self):
        self.none_value_test('required')
    
    def test_none_value_passes_optional(self):
        self.none_value_test('optional')
    
    def unlimited_test(self, parameter_name):
        self.ioprocessor.verify(
            iovalue=[object()],
            unlimited=True,
            **{parameter_name: []}
            )
    
    def test_unlimited_required(self):
        self.unlimited_test('required')
    
    def test_unlimited_optional(self):
        self.unlimited_test('optional')

class TestIOSpecTupleVerify(unittest.TestCase):
    """ Confirm that tuples are treated the same as lists, both when used as
        'iospec' and 'iovalue'. """

class TestIOSpecListCoerce(CoercionTest):
    def coercion_test(self, parameter_name):
        result_list = self.ioprocessor.coerce(
            iovalue=[self.BeforeCoercionType()],
            **{parameter_name: [self.YesCoercionType]}
            )
        result = result_list[0]
        
        assert isinstance(result, self.YesCoercionType)
    
    def test_coercion_required(self):
        self.coercion_test('required')
    
    def test_coercion_optional(self):
        self.coercion_test('optional')

class TestIOSpecListVerifyNested(unittest.TestCase):
    """ Confirm that nested container types behave as expected. """
    def make_nested_iospec(self, iospec):
        return [iospec]
    
    def make_nested_iovalue(self, value):
        return [value]
    
    def iospec_test(self, parameter_name, iovalue, iospec):
        IOProcessor().verify(
            iovalue=self.make_nested_iovalue(iovalue),
            **{parameter_name: self.make_nested_iospec(iospec)}
            )
    
    # ----------------------- Nested list tests ------------------------
    
    def list_passes_test(self, parameter_name, iovalue):
        self.iospec_test(parameter_name, iovalue, [object])
    
    def list_expected_passes_test(self, parameter_name):
        self.list_passes_test(parameter_name, [object()])
    
    def test_list_expected_passes_required(self):
        self.list_expected_passes_test('required')
    
    def test_list_expected_passes_optional(self):
        self.list_expected_passes_test('optional')
    
    def test_list_missing_item_passes_optional(self):
        self.list_passes_test('optional', [])
    
    def list_raises_test(self, *pargs, **kwargs):
        with pytest.raises(VerificationFailureError):
            self.list_passes_test(*pargs, **kwargs)
    
    def list_extra_item_raises_test(self, parameter_name):
        self.list_raises_test(parameter_name, [object(), object()])
    
    def test_list_extra_item_raises_required(self):
        self.list_extra_item_raises_test('required')
    
    def test_list_extra_item_raises_optional(self):
        self.list_extra_item_raises_test('optional')
    
    def test_list_missing_item_raises_required(self):
        self.list_raises_test('required', [])
    
    # ----------------------- Nested dict tests ------------------------
    
    def dict_passes_test(self, parameter_name, iovalue):
        self.iospec_test(parameter_name, iovalue, {'a': object})
    
    def dict_expected_passes_test(self, parameter_name):
        self.dict_passes_test(parameter_name, {'a': object()})
    
    def test_dict_expected_passes_required(self):
        self.dict_expected_passes_test('required')
    
    def test_dict_expected_passes_optional(self):
        self.dict_expected_passes_test('optional')
    
    def test_dict_missing_item_passes_optional(self):
        self.dict_passes_test('optional', {})
    
    def dict_raises_test(self, *pargs, **kwargs):
        with pytest.raises(VerificationFailureError):
            self.dict_passes_test(*pargs, **kwargs)
    
    def dict_extra_item_raises_test(self, parameter_name):
        self.dict_raises_test(parameter_name, {'a': object(), 'b': object()})
    
    def test_dict_extra_item_raises_required(self):
        self.dict_extra_item_raises_test('required')
    
    def test_dict_extra_item_raises_optional(self):
        self.dict_extra_item_raises_test('optional')
    
    def test_dict_missing_item_raises_required(self):
        self.dict_raises_test('required', {})



# ---------------------- Dictionary keys checking ----------------------

class VerificationTest(unittest.TestCase):
    class CustomType(object):
        pass
    
    class InvalidType(object):
        pass
    
    def good_iovals_test(self, iovals):
        IOProcessor().verify(iovals, **self.trial_iospecs())
    
    def bad_iovals_test(self, iovals):
        with pytest.raises(VerificationFailureError):
            self.good_iovals_test(iovals)
    
    def trial_iospecs(self):
        return dict(
            optional={},
            required={},
            unlimited=False,
            )

class BasicIOSpecTest(VerificationTest):
    @classmethod
    def required_iovals(cls):
        return dict(a=0, b=1, c=2)
    
    @classmethod
    def optional_iovals(cls):
        return dict(d=3, e=4, f=5)
    
    @classmethod
    def required_iospec(cls):
        return {'a': int, 'b': int, 'c': int}
    
    @classmethod
    def optional_iospec(cls):
        return {'d': int, 'e': int, 'f': int}
    
    @classmethod
    def all_iovals(cls):
        result = cls.required_iovals()
        result.update(cls.optional_iovals())
        return result

class TestRequiredIOSpec(BasicIOSpecTest):
    def trial_iospecs(self):
        return dict(
            required=self.required_iospec()
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

class TestOptionalIOSpec(BasicIOSpecTest):
    def trial_iospecs(self):
        return dict(optional=self.optional_iospec())
    
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

class TestUnlimitedIOVals(BasicIOSpecTest):
    def trial_iospecs(self):
        return dict(unlimited=True)
    
    def test_empty_iovals_passes(self):
        self.good_iovals_test(iovals={})
    
    def test_many_iovals_passes(self):
        keys = list(string.ascii_lowercase)
        iovals = dict(zip(keys, range(len(keys))))
        self.good_iovals_test(iovals)

class TestRequiredAndOptionalBoth(BasicIOSpecTest):
    def trial_iospecs(self):
        return dict(
            required=self.required_iospec(),
            optional=self.optional_iospec(),
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



# ------------------------- ListOf iospec tests -------------------------

class TestListOf(VerificationTest):
    def trial_iospecs(self):
        return dict(
            required={
                'a': iomanager.ListOf(int)
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
    def listof_iospec(self):
        return {
            'a': iomanager.ListOf(
                    {'a': int,}
                )
            }
    
    def trial_iospecs(self):
        return {
            self.iospec_parameter_qualifier: self.listof_iospec()
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

class TestListOfStructuredOptional(ListOfStructuredTest, VerificationTest):
    iospec_parameter_qualifier = 'optional'

class TestListOfStructuredRequired(ListOfStructuredTest, VerificationTest):
    iospec_parameter_qualifier = 'required'
    
    def test_missing_key_passes(self):
        iovals = self.good_iovals()
        del iovals['a'][0]['a']
        self.bad_iovals_test(iovals)

class ListOfStructuredNestedTest(object):
    def listof_iospec(self):
        return {
            'a':  iomanager.ListOf(
                {
                    'a': {
                        'b': int
                    }
                }
            )
        }
    
    def trial_iospecs(self):
        return {
            self.iospec_parameter_qualifier: self.listof_iospec()
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

class TestListOfStructuredNestedOptional(ListOfStructuredNestedTest, VerificationTest):
    iospec_parameter_qualifier = 'optional'

class TestListOfStructuredNestedRequired(ListOfStructuredNestedTest, VerificationTest):
    iospec_parameter_qualifier = 'required'
    
    def test_missing_nested_key_raises(self):
        iovals = self.good_iovals()
        del iovals['a'][0]['a']['b']
        self.bad_iovals_test(iovals)

class TestListOfNestedListOf(VerificationTest):
    def trial_iospecs(self):
        return dict(
            required={
                'a': iomanager.ListOf(
                    iomanager.ListOf(int)
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



# ----------------------- Structured iospec tests -----------------------

class StructuredDictTest(VerificationTest):
    """ 'StructuredDict' here means that the iospec dictionary includes values
        that are nested iospec dictionaries. """
    @classmethod
    def make_iovals(cls):
        return {
            'a': {'b': 2, 'c': 3},
            }
    
    @classmethod
    def make_iospec(cls):
        return {
            'a': {'b': int, 'c': int},
            }
    
    def none_value_raises_test(self):
        iovals = self.make_iovals()
        iovals['a'] = None
        self.bad_iovals_test(iovals)

class TestStructuredDictRequired(StructuredDictTest):
    def trial_iospecs(self):
        return dict(
            required=self.make_iospec()
            )
    
    def test_ok_iovals(self):
        self.good_iovals_test(self.make_iovals())
    
    def test_none_value_raises(self):
        self.none_value_raises_test()
    
    def test_missing_structured_ioval_raises(self):
        iovals = self.make_iovals()
        del iovals['a']
        self.bad_iovals_test(iovals)
    
    def test_missing_nested_ioval_raises(self):
        iovals = self.make_iovals()
        del iovals['a']['b']
        self.bad_iovals_test(iovals)
    
    def test_extra_nested_ioval_raises(self):
        iovals = self.make_iovals()
        iovals['a']['xxx'] = 9
        self.bad_iovals_test(iovals)

class TestStructuredDictOptional(StructuredDictTest):
    def trial_iospecs(self):
        return dict(
            optional=self.make_iospec()
            )
    
    def test_ok_iovals(self):
        self.good_iovals_test(self.make_iovals())
    
    def test_none_value_raises(self):
        self.none_value_raises_test()
    
    def test_empty_iovals_passes(self):
        self.good_iovals_test(iovals={})
    
    def test_missing_structured_ioval_passes(self):
        iovals = self.make_iovals()
        del iovals['a']
        self.good_iovals_test(iovals)
    
    def test_missing_nested_ioval_passes(self):
        iovals = self.make_iovals()
        del iovals['a']['b']
        self.good_iovals_test(iovals)
    
    def test_extra_nested_ioval_raises(self):
        iovals = self.make_iovals()
        iovals['a']['xxx'] = 9
        self.bad_iovals_test(iovals)

class TestStructuredDictRequiredEmpty(VerificationTest):
    def trial_iospecs(self):
        return dict(
            required={'a': {}}
            )
    
    def test_ok_iovals_passes(self):
        self.good_iovals_test({'a': {}})
    
    def test_missing_structured_ioval_raises(self):
        self.bad_iovals_test({})
    
    def test_extra_nested_ioval_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredDictOptionalEmpty(VerificationTest):
    def trial_iospecs(self):
        return dict(
            optional={'a': {}}
            )
    
    def test_ok_iovals_passes(self):
        self.good_iovals_test({'a': {}})
    
    def test_missing_structured_ioval_passes(self):
        self.good_iovals_test({})
    
    def test_extra_nested_ioval_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredDictUnlimited(VerificationTest):
    """ When 'unlimited' is True, only top-level keyword arguments are
        unlimited. StructuredDict data should still be checked for unknown keyword
        arguments. """
    
    def trial_iospecs(self):
        return dict(
            optional={'a': {'b': int}},
            unlimited=True
            )
    
    def test_extra_kwarg_passes(self):
        self.good_iovals_test({'x': 1})
    
    def test_extra_nested_kwarg_raises(self):
        self.bad_iovals_test({'a': {'x': 1}})

class TestStructuredDictRequiredOverridesOptional(VerificationTest):
    """ When structured iospec keys appear in both the 'required' and the
        'optional' iospecs, the 'required' condition should take precedence. """
    @classmethod
    def required_iospec(cls):
        return {
            'a': int,
            'b': {'x': int, 'y': int},
            'c': {
                'q': {'m': int},
                'r': {'n': int},
                },
            }
    
    @classmethod
    def optional_iospec(cls):
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
    
    def trial_iospecs(self):
        return dict(
            required=self.required_iospec(),
            optional=self.optional_iospec(),
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

class TypeCheckingTest(unittest.TestCase):
    """ Confirm that coercion behaves correctly when the iospec 'type object' is
        a 'class' object. """
    
    class CustomType(object):
        """ A custom type for testing type-checking. """
    
    class CustomSubclassType(CustomType):
        """ A custom type for testing type-checking. """
    
    class InvalidType(object):
        """ A custom type for testing type-checking. """

class TypeCheckingExtendedTest(object):
    def call_process_method(self, value):
        ioprocessor = IOProcessor()
        
        iovals = {
            'a': self.make_extended_ioval(value)
            }
        
        required = {
            'a': self.make_extended_iospec()
            }
        
        ioprocessor.verify(
            iovalue=iovals,
            required=required
            )
    
    def test_correct_type_passes(self):
        self.call_process_method(self.CustomType())
    
    def test_invalid_type_raises(self):
        with pytest.raises(VerificationFailureError):
            self.call_process_method(self.InvalidType())

class TestTypeCheckingStructured(TypeCheckingTest, TypeCheckingExtendedTest):
    """ Confirm that type checking is occurring when the iospec 'type object' is
        a dictionary. """
    
    def make_extended_ioval(self, value):
        return {'b': value}
    
    def make_extended_iospec(self):
        return {'b': self.CustomType}

class TestTypeCheckingListOf(TypeCheckingTest, TypeCheckingExtendedTest):
    """ Confirm that type checking is occurring when the iospec 'type object' is
        a ListOf instance. """
    
    def make_extended_ioval(self, value):
        return [value]
    
    def make_extended_iospec(self):
        return iomanager.ListOf(self.CustomType)



# ------------------------ Type coercion tests -------------------------

def retrieve_location(location_tuple, container):
    if not isinstance(location_tuple, tuple):
        location_tuple = (location_tuple,)
    
    this_index = location_tuple[0]
    remainder = location_tuple[1:]
    
    if isinstance(container, iomanager.ListOf):
        target_value = container.iospec_obj
    else:
        target_value = container[this_index]
    
    if not remainder:
        return target_value
    
    return retrieve_location(remainder, target_value)

class TypeCoercionTest(unittest.TestCase):
    def get_coercion_result(self, iospecs=None, iovals=None):
        coercion_functions = self.get_coercion_functions()
        ioprocessor = IOProcessor(
            coercion_functions=self.get_coercion_functions()
            )
        
        iospecs = iospecs or self.get_iospecs()
        iovals = iovals or self.get_iovals()
        
        return ioprocessor.coerce(iovals, **iospecs)
    
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

class TypeCoercionVerificationTest(TypeCoercionTest):
    """ A test to confirm that calling IOProcessor.coerce() uses the coercion
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

class TestTypeCoercionArguments(TypeCoercionVerificationTest):
    """ Confirm coercion for each of 'required', 'optional', and
        'unlimited' arguments. """
    
    def get_iovals(self):
        return {'a': self.BeforeCoercionType()}
    
    def make_iospecs(self, iospec_kind, **kwargs):
        result = {
            iospec_kind: {
                'a': self.YesCoercionType
                }
            }
        result.update(kwargs)
        return result
    
    def coercion_test(self, iospecs):
        self.type_test('a', self.YesCoercionType, iospecs=iospecs)
    
    def coercion_argument_test(self, iospec_kind):
        iospecs = self.make_iospecs(iospec_kind)
        
        self.coercion_test(iospecs)
    
    def test_coercion_required(self):
        self.coercion_argument_test('required')
    
    def test_coercion_optional(self):
        self.coercion_argument_test('optional')

class TestTypeCoercionRequiredOverridesOptional(TypeCoercionVerificationTest):
    """ Confirm that when 'required' and 'optional' are both
        present, 'required' overrides 'optional. """
    
    def get_iospecs(self):
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
    
    def coercion_test(self, type_obj, value, expected):
        iospecs = {
            'required': {'a': type_obj}
            }
        iovals = {'a': value}
        
        result = self.get_result_value('a', iospecs=iospecs, iovals=iovals)
        
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
        
        type_obj = iomanager.ListOf(unicode)
        self.coercion_test(type_obj, trial_list, expected)

class TypeCoercionDefaultFunctionsTest(unittest.TestCase):
    """ Confirm that the default type coercion functions behave as expected. """
    class ArbitraryType(object):
        """ This class is used to test a coercion function's effect upon an
            arbitrarily-typed value. """
    
    def coercion_test(self, type_obj, value, expected):
        coercion_function = self.coercion_functions[type_obj]
        
        result = coercion_function(value)
        assert result == expected
    
    def arbitrary_value_test(self, type_obj):
        class ArbitraryType(object):
            """ An arbitrary type which should pass through coercion
                unchanged. """
        arbitrary_value = self.ArbitraryType()
        self.coercion_test(type_obj, arbitrary_value, arbitrary_value)

class TestTypeCoercionDefaultFunctionsInput(TypeCoercionDefaultFunctionsTest):
    """ Confirm that input values coerce correctly. """
    coercion_functions = iomanager.json_tools.input_coercion_functions
    
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
            value=dt_string,
            expected=dt_value,
            )
    
    #def test_dtdate_gets_string(self):
    #    pass
    
    def test_uuid_gets_string(self):
        uuid_value = uuid.uuid4()
        uuid_string = str(uuid_value)
        self.coercion_test(
            uuid.UUID,
            value=uuid_string,
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
    coercion_functions = iomanager.json_tools.output_coercion_functions
    
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
            value=dt_value,
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
            value=uuid_value,
            expected=uuid_string,
            )

class TestTypeCoercionCycle(unittest.TestCase):
    """ Confirm that certain types are preserved through the coercion 'cycle'.
        
        When these types are coerced to output, then coerced back to input, the
        result is equal to the starting value. """
    
    def coercion_cycle_test(self, type_obj, starting_value):
        output_processor = iomanager.json_tools.output_processor()
        input_processor = iomanager.json_tools.input_processor()
        
        iospec =  {'value': type_obj}
        
        output_result = output_processor.coerce(
            iovalue={'value': starting_value},
            required=iospec,
            )
        
        final_result = input_processor.coerce(
            iovalue=output_result,
            required=iospec,
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



# -------------------------- IOManager tests ---------------------------

class IOManagerTest(unittest.TestCase):
    """ Test the 'IOManager' class. """
    def process_test(
        self,
        iomanager,
        process_kind,
        iospec,
        iovals,
        expected=None,
        ):
        method_name = 'process_' + process_kind
        process_method = getattr(iomanager, method_name)
        result = process_method(iovals, required=iospec)
        assert result == expected

class TestIOManagerProcessBasic(IOManagerTest):
    def no_coercion_test(self, process_kind):
        iomanager = IOManager()
        
        iospec = {'a': object}
        expected = {'a': object()}
        iovals = expected.copy()
        
        self.process_test(iomanager, process_kind, iospec, iovals, expected)
    
    def test_process_input(self):
        self.no_coercion_test('input')
    
    def test_process_output(self):
        self.no_coercion_test('output')

class TestIOManagerProcessCoercion(IOManagerTest):
    class ExternalType(object):
        """ This type is used by an external process. Upon input, it must be
            coerced to 'InternalType'. """
    
    class InternalType(object):
        """ This type is used by an internal process. Upon output, it must be
            coerced to 'ExternalType'. """
    
    def yes_coercion_test(
        self,
        process_kind,
        coercion_function,
        iovals,
        expected
        ):
        iomanager = IOManager(
            coercion_functions={self.InternalType: coercion_function}
            )
        
        iospec = {'a': self.InternalType}
        
        self.process_test(iomanager, process_kind, iospec, iovals, expected)
    
    def test_process_input(self):
        expected_value = self.InternalType()
        
        def coercion_function(value):
            return expected_value
        
        iovals = {'a': self.ExternalType()}
        expected = {'a': expected_value}
        
        self.yes_coercion_test('input', coercion_function, iovals, expected)
    
    def test_process_output(self):
        expected_value = self.ExternalType()
        
        def coercion_function(value):
            return expected_value
        
        iovals = {'a': self.InternalType()}
        expected = {'a': expected_value}
        
        self.yes_coercion_test('output', coercion_function, iovals, expected)

class TestIOManagerProcessTypecheck(IOManagerTest):
    def typecheck_test(self, process_kind):
        class ExpectedType(object):
            pass
        
        def reject_all(value, expected_type):
            raise ConfirmationError
        
        iomanager = IOManager(
            typecheck_functions={ExpectedType: reject_all}
            )
        
        iospec = {'a': ExpectedType}
        iovals = {'a': ExpectedType()}
        
        with pytest.raises(ConfirmationError):
            self.process_test(iomanager, process_kind, iospec, iovals)
    
    def test_process_input(self):
        self.typecheck_test('input')
    
    def test_process_output(self):
        self.typecheck_test('output')

class IOManagerPrecedenceTest(IOManagerTest):
    def precedence_test(self, process_stage, process_kind):
        class ExpectedType(object):
            pass
        
        overridden_function, confirmed_function = self.make_functions()
        
        init_kwargs = {
            '{}_functions'.format(process_stage): {
                ExpectedType: overridden_function,
                },
            '{}_{}_functions'.format(process_kind, process_stage): {
                ExpectedType: confirmed_function,
                },
            }
        
        iomanager = IOManager(**init_kwargs)
        
        iospec = {'a': ExpectedType}
        iovals = {'a': ExpectedType()}
        
        with pytest.raises(ConfirmationError):
            self.process_test(iomanager, process_kind, iospec, iovals)

class TestIOManagerPrecedenceCoercion(IOManagerPrecedenceTest):
    """ Confirm that 'input_coercion_functions' and 'output_coercion_functions'
        each override 'coercion_functions'. """
    
    def make_functions(self):
        def overridden_function(value):
            pass
        
        def confirmed_function(value):
            raise ConfirmationError
        
        return overridden_function, confirmed_function
    
    def test_input_coercion_functions_overrides(self):
        self.precedence_test('coercion', 'input')
    
    def test_output_coercion_functions_overrides(self):
        self.precedence_test('coercion', 'output')

class TestIOManagerPrecedenceTypecheck(IOManagerPrecedenceTest):
    """ Confirm that 'input_typecheck_functions' and
        'output_typecheck_functions' each override 'typecheck_functions'. """
    
    def make_functions(self):
        def overridden_function(value, expected_type):
            pass
        
        def confirmed_function(value, expected_type):
            raise ConfirmationError
        
        return overridden_function, confirmed_function
    
    def test_input_typecheck_functions_overrides(self):
        self.precedence_test('typecheck', 'input')
    
    def test_output_typecheck_functions_overrides(self):
        self.precedence_test('typecheck', 'output')

class TestIOManagerMethods(unittest.TestCase):
    """ Test the separate 'coerce' and 'verify' methods. """
    def method_test(self, method_name):
        iomanager = IOManager()
        method_callable = getattr(iomanager, method_name)
        method_callable(iovalue={})
    
    def test_coerce_input(self):
        self.method_test('coerce_input')
    
    def test_coerce_output(self):
        self.method_test('coerce_output')
    
    def test_verify_input(self):
        self.method_test('verify_input')
    
    def test_verify_output(self):
        self.method_test('verify_output')







