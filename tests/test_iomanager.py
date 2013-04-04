""" Copyright (c) 2013 Josh Matthias <python.iomanager@gmail.com> """

import pytest
import unittest
import string
from contextlib import contextmanager

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

class BeforeCoercionType(object):
    """ A type that coerces to YesCoercionType. """

class YesCoercionType(object):
    """ A type with a custom coercion function. """

def coerce_custom(value):
    if isinstance(value, BeforeCoercionType):
        return YesCoercionType()
    return value

# --------------------------- Baseline tests ---------------------------

class TestVerifyNoIOSpec(unittest.TestCase):
    """ When no 'iospec' values are given, verification passes. """
    
    def test_no_iospec_passes(self):
        IOProcessor().verify(
            iovalue=object()
            )

class TestCoerceNoIOSpec(unittest.TestCase):
    def test_no_iospec_passes(self):
        IOProcessor().coerce(
            iovalue=object()
            )



# ------------------------ Type-checking tests -------------------------

class VerifyTypeCheckBaseTest(object):
    def correct_type_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=self.wrap_iovalue(object()),
            **{parameter_name: self.wrap_iospec(object)}
            )
    
    def test_correct_type_passes_required(self):
        self.correct_type_passes_test('required')
    
    def test_correct_type_passes_optional(self):
        self.correct_type_passes_test('optional')
    
    def correct_type_subclass_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=self.wrap_iovalue(CustomSubclassType()),
            **{parameter_name: self.wrap_iospec(CustomType)}
            )
    
    def test_correct_type_subclass_passes_required(self):
        self.correct_type_subclass_passes_test('required')
    
    def test_correct_type_subclass_passes_optional(self):
        self.correct_type_subclass_passes_test('optional')
    
    def wrong_type_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            IOProcessor().verify(
                iovalue=self.wrap_iovalue(object()),
                **{parameter_name: self.wrap_iospec(CustomType)}
                )
    
    def test_wrong_type_raises_required(self):
        self.wrong_type_raises_test('required')
    
    def test_wrong_type_raises_optional(self):
        self.wrong_type_raises_test('optional')
    
    def anytype_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=self.wrap_iovalue(object()),
            **{parameter_name: self.wrap_iospec(iomanager.AnyType)}
            )
    
    def test_anytype_passes_required(self):
        self.anytype_passes_test('required')
    
    def test_anytype_passes_optional(self):
        self.anytype_passes_test('optional')
    
    def test_required_overrides_optional(self):
        IOProcessor().verify(
            iovalue=self.wrap_iovalue(object()),
            required=self.wrap_iospec(object),
            optional=self.wrap_iospec(CustomType),
            )
    
    def custom_function_test(self, value, custom_function):
        """ Confirm type checking behavior when custom type-checking functions
            are in use. """
        ioprocessor = IOProcessor(
            typecheck_functions={CustomType: custom_function}
            )
        ioprocessor.verify(
            iovalue=self.wrap_iovalue(value),
            required=self.wrap_iospec(CustomType),
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
            self.custom_function_test(CustomType(), reject_value)
    
    def test_type_check_success_error(self):
        """ When a custom type-checking function raises a TypeCheckSuccessError,
            type checking passes even if the value would have been rejected
            normally. """
        def accept_value(value, expected_type):
            raise TypeCheckSuccessError
        self.custom_function_test(object(), accept_value)
    
    def none_value_passes_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=self.wrap_iovalue(None),
            **{parameter_name: self.wrap_iospec(object)}
            )

class VerifyTypeCheckStandardTest(VerifyTypeCheckBaseTest):
    """ Applies to 'dict', 'list', 'tuple', 'nested'. """
    
    def test_none_value_passes_required(self):
        self.none_value_passes_test('required')
    
    def test_none_value_passes_optional(self):
        self.none_value_passes_test('optional')

class VerifyTypeCheckRejectNoneValuesTest(VerifyTypeCheckBaseTest):
    """ Applies to 'ListOf'. """
    
    def none_value_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            self.none_value_passes_test(parameter_name)
    
    def test_none_value_raises_required(self):
        self.none_value_raises_test('required')
    
    def test_none_value_raises_optional(self):
        self.none_value_raises_test('optional')

class TestVerifyTypeCheckNonContainerIOSpec(
    VerifyTypeCheckStandardTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return iospec
    
    def wrap_iovalue(self, iovalue):
        return iovalue

class TestVerifyTypeCheckListIOSpec(
    VerifyTypeCheckStandardTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return [iospec]
    
    def wrap_iovalue(self, iovalue):
        return [iovalue]

class TestVerifyTypeCheckTupleIOSpec(
    VerifyTypeCheckStandardTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return tuple([iospec])
    
    def wrap_iovalue(self, iovalue):
        return tuple([iovalue])

class TestVerifyTypeCheckDictIOSpec(
    VerifyTypeCheckStandardTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return {'a': iospec}
    
    def wrap_iovalue(self, iovalue):
        return {'a': iovalue}

class TestVerifyTypeCheckListOfIOSpec(
    VerifyTypeCheckRejectNoneValuesTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return iomanager.ListOf(iospec)
    
    def wrap_iovalue(self, iovalue):
        return [iovalue]

class TestVerifyTypeCheckNestedIOSpec(
    VerifyTypeCheckStandardTest,
    unittest.TestCase,
    ):
    def wrap_iospec(self, iospec):
        return {'a': {'b': iospec}}
    
    def wrap_iovalue(self, iovalue):
        return {'a': {'b': iovalue}}



# ---------------------- Structure-checking tests ----------------------

class TestVerifyStructureNonContainerIOSpec(unittest.TestCase):
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
    
    def test_unlimited_ignored_no_iospec(self):
        """ When no 'iospec' is provided, verification and 'unlimited' is ignored
            ('True' and 'False' both pass).
            
            Similar to the situation with non-container IOSpecs."""
        IOProcessor().verify(
            iovalue=object(),
            unlimited=True,
            )
    
class VerifyStructureBasicTest(object):
    """ Applies to all container types. """
    def empty_test(self, parameter_name, iovalue):
        IOProcessor().verify(
            iovalue=iovalue,
            **{parameter_name: self.make_iospec(0)}
            )
    
    def empty_gets_empty_passes_test(self, parameter_name):
        self.empty_test(parameter_name, self.make_iovalue(0))
    
    def test_empty_gets_empty_passes_required(self):
        self.empty_gets_empty_passes_test('required')
    
    def test_empty_gets_empty_passes_optional(self):
        self.empty_gets_empty_passes_test('optional')
    
    def empty_gets_none_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            self.empty_test(parameter_name, None)
    
    def test_empty_gets_none_raises_required(self):
        self.empty_gets_none_raises_test('required')
    
    def test_empty_gets_none_raises_optional(self):
        self.empty_gets_none_raises_test('optional')
    
    def parameter_test(self, parameter_name, iovalue):
        IOProcessor().verify(
            iovalue=iovalue,
            **{parameter_name: self.make_iospec(1)}
            )
    
    def expected_iovalue_passes_test(self, parameter_name):
        self.parameter_test(parameter_name, self.make_iovalue(1))
    
    def test_expected_required_passes(self):
        self.expected_iovalue_passes_test('required')
    
    def test_expected_optional_passes(self):
        self.expected_iovalue_passes_test('optional')
    
class VerifyStructureStrictTest(object):
    """ Applies to 'list', 'tuple', 'dict', 'nested'. """
    def extra_item_raises_test(self, parameter_name):
        with pytest.raises(VerificationFailureError):
            self.parameter_test(parameter_name, self.make_iovalue(2))
    
    def test_extra_item_raises_required(self):
        self.extra_item_raises_test('required')
    
    def test_extra_item_raises_optional(self):
        self.extra_item_raises_test('optional')
    
    def missing_item_test(self, parameter_name):
        self.parameter_test(parameter_name, self.make_iovalue(0))
    
    def test_missing_item_raises_required(self):
        with pytest.raises(VerificationFailureError):
            self.missing_item_test('required')
    
    def test_missing_item_passes_optional(self):
        self.missing_item_test('optional')
    
    def test_required_overrides_optional(self):
        with pytest.raises(VerificationFailureError):
            IOProcessor().verify(
                iovalue=self.make_iovalue(0),
                required=self.make_iospec(1),
                optional=self.make_iospec(1),
                )
    
    def test_optional_extends_required(self):
        IOProcessor().verify(
            iovalue=self.make_iovalue(2),
            required=self.make_iospec(1),
            optional=self.make_iospec(2),
            )

class VerifyStructureUnlimitedTest(object):
    """ Applies to 'list', 'tuple', 'dict'. """
    def unlimited_test(self, parameter_name):
        IOProcessor().verify(
            iovalue=self.make_iovalue(1),
            unlimited=True,
            **{parameter_name: self.make_iospec(0)}
            )
    
    def test_unlimited_required(self):
        self.unlimited_test('required')
    
    def test_unlimited_optional(self):
        self.unlimited_test('optional')

class TestVerifyStructureListIOSpec(
    VerifyStructureBasicTest,
    VerifyStructureStrictTest,
    VerifyStructureUnlimitedTest,
    unittest.TestCase,
    ):
    def make_iospec(self, length):
        return [object for i in range(length)]
    
    def make_iovalue(self, length, maker=object):
        return [maker() for i in range(length)]

class TestVerifyStructureTupleIOSpec(
    VerifyStructureBasicTest,
    VerifyStructureStrictTest,
    VerifyStructureUnlimitedTest,
    unittest.TestCase,
    ):
    def make_iospec(self, length):
        return tuple([object for i in range(length)])
    
    def make_iovalue(self, length, maker=object):
        return tuple([maker() for i in range(length)])

class TestVerifyStructureDictIOSpec(
    VerifyStructureBasicTest,
    VerifyStructureStrictTest,
    VerifyStructureUnlimitedTest,
    unittest.TestCase,
    ):
    def make_iospec(self, length):
        keys = list('abc')
        return {keys[i]: object for i in range(length)}
    
    def make_iovalue(self, length, maker=object):
        keys = list('abc')
        return {keys[i]: maker() for i in range(length)}

class TestVerifyStructureListOfIOSpec(
    VerifyStructureBasicTest,
    unittest.TestCase,
    ):
    def make_iospec(self, length):
        return iomanager.ListOf(object)
    
    def make_iovalue(self, length, maker=object):
        return [maker() for i in range(length)]

class TestVerifyStructureNestedIOSpec(
    VerifyStructureBasicTest,
    VerifyStructureStrictTest,
    unittest.TestCase,
    ):
    def make_iospec(self, length):
        keys = list('abc')
        return {'x': {keys[i]: object for i in range(length)}}
    
    def make_iovalue(self, length, maker=object):
        keys = list('abc')
        return {'x': {keys[i]: maker() for i in range(length)}}
    
    def unlimited_extra_nested_item_raises_test(self, parameter_name):
        """ When 'unlimited' is True, only top-level keyword arguments are
            unlimited. 'dict'-type iovalues should still be checked for unknown
            keys. """
        with pytest.raises(VerificationFailureError):
            IOProcessor().verify(
                iovalue=self.make_iovalue(2),
                unlimited=True,
                **{parameter_name: self.make_iospec(1)}
                )
    
    def test_unlimited_extra_nested_item_raises_required(self):
        self.unlimited_extra_nested_item_raises_test('required')
    
    def test_unlimited_extra_nested_item_raises_optional(self):
        self.unlimited_extra_nested_item_raises_test('optional')



# --------------------------- Coercion tests ---------------------------

class CoercionTestCase(unittest.TestCase):
    def setUp(self):
        self.ioprocessor = IOProcessor(
            coercion_functions={YesCoercionType: coerce_custom}
            )

class CoercionTest(object):
    def no_coercion_test(self, parameter_name):
        uncoerced_value = BeforeCoercionType()
        
        coercion_result = self.ioprocessor.coerce(
            iovalue=self.wrap_iovalue(uncoerced_value),
            **{parameter_name: self.wrap_iospec(object)}
            )
        
        result = self.retrieve_result(coercion_result)
        
        assert result is uncoerced_value
    
    def test_no_coercion_required(self):
        self.no_coercion_test('required')
    
    def test_no_coercion_optional(self):
        self.no_coercion_test('optional')
    
    def yes_coercion_test(self, parameter_name):
        coercion_result = self.ioprocessor.coerce(
            iovalue=self.wrap_iovalue(BeforeCoercionType()),
            **{parameter_name: self.wrap_iospec(YesCoercionType)}
            )
        
        result = self.retrieve_result(coercion_result)
        
        assert isinstance(result, YesCoercionType)
    
    def test_yes_coercion_required(self):
        self.yes_coercion_test('required')
    
    def test_yes_coercion_optional(self):
        self.yes_coercion_test('optional')
    
    def test_required_overrides_optional(self):
        uncoerced_value = BeforeCoercionType()
        
        coercion_result = self.ioprocessor.coerce(
            iovalue=self.wrap_iovalue(uncoerced_value),
            required=self.wrap_iospec(YesCoercionType),
            optional=self.wrap_iospec(object),
            )
        
        result = self.retrieve_result(coercion_result)
        
        assert isinstance(result, YesCoercionType)

class TestCoerceNonContainerIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return iospec
    
    def wrap_iovalue(self, iovalue):
        return iovalue
    
    def retrieve_result(self, coercion_result):
        return coercion_result

class TestCoerceListIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return [iospec]
    
    def wrap_iovalue(self, iovalue):
        return [iovalue]
    
    def retrieve_result(self, coercion_result):
        return coercion_result[0]

class TestCoerceTupleIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return tuple([iospec])
    
    def wrap_iovalue(self, iovalue):
        return tuple([iovalue])
    
    def retrieve_result(self, coercion_result):
        return coercion_result[0]

class TestCoerceDictIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return {'a': iospec}
    
    def wrap_iovalue(self, iovalue):
        return {'a': iovalue}
    
    def retrieve_result(self, coercion_result):
        return coercion_result['a']

class TestCoerceListOfIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return iomanager.ListOf(iospec)
    
    def wrap_iovalue(self, iovalue):
        return [iovalue]
    
    def retrieve_result(self, coercion_result):
        return coercion_result[0]

class TestCoerceNestedIOSpec(CoercionTest, CoercionTestCase):
    def wrap_iospec(self, iospec):
        return {'a': {'b': iospec}}
    
    def wrap_iovalue(self, iovalue):
        return {'a': {'b': iovalue}}
    
    def retrieve_result(self, coercion_result):
        return coercion_result['a']['b']

class TestCoercionContainersPreserved(unittest.TestCase):
    def preservation_test(self, parameter_name, initial, expected, iospec):
        result = IOProcessor().coerce(
            iovalue=initial,
            **{parameter_name: iospec}
            )
        
        assert result == expected
    
    def dict_preserved_test(self, parameter_name):
        keys = string.lowercase
        initial = {ikey: object() for ikey in keys}
        expected = initial.copy()
        iospec = {ikey: object for ikey in keys}
        
        self.preservation_test(parameter_name, initial, expected, iospec)
    
    def test_dict_preserved_required(self):
        self.dict_preserved_test('required')
    
    def test_dict_preserved_optional(self):
        self.dict_preserved_test('optional')
    
    def list_preserved_test(self, parameter_name):
        """ When a list is provided as an 'iovalue' value, its length and order
            are preserved.
            
            It is important that the list in this test case is not in a
            'naturally-sorted' order. Otherwise, the coercion function wouldn't
            need to preserve the input order; it would only need to call
            'sorted()' on the result, and it could get lucky. """
        initial = list(u'aWMp8CAjRjMd039Hy1o4fLCv0RsVZxTB')
        expected = list(initial)
        iospec = [object for i in initial]
        
        self.preservation_test(parameter_name, initial, expected, iospec)
    
    def test_list_preserved_required(self):
        self.list_preserved_test('required')
    
    def test_list_preserved_optional(self):
        self.list_preserved_test('optional')



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
    """ Check that 'coercion' and 'typecheck' functions provided to '__init__'
        override each other as expected. """
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



# ----------------------- __init__ defaults tests ------------------------

class IOProcessorStashDefaultsTestCase(unittest.TestCase):
    """ When 'required', 'optional', and 'unlimited' are provided to '__init__',
        they are used as default argument values to 'verify' and 'coerce'. """
    def get_method(self, parameter_name, parameter_value, **kwargs):
        method_name = self.operation_name
        kwargs.update({parameter_name: parameter_value})
        processor = IOProcessor(**kwargs)
        return getattr(processor, method_name)

class IOManagerStashDefaultsTestCase(unittest.TestCase):
    """ When 'input_required', 'output_required', etc. are provided to
        '__init__', they are used as default argument values to 'verify_input',
        'verify_output', etc. """
    def get_method(self, parameter_name, parameter_value, **kwargs):
        full_parameter_name = '_'.join([self.phase_name, parameter_name])
        method_name = '_'.join([self.operation_name, self.phase_name])
        
        kwargs.update({full_parameter_name: parameter_value})
        manager = IOManager(**kwargs)
        return getattr(manager, method_name)

class StashDefaultsVerifyTest(object):
    def default_test(self, parameter_name):
        method = self.get_method(parameter_name, CustomType)
        with pytest.raises(VerificationFailureError):
            method(iovalue=object())
    
    def override_test(self, parameter_name):
        method = self.get_method(parameter_name, CustomType)
        method(iovalue=object(), **{parameter_name: object})
    
    def test_default_required(self):
        self.default_test('required')
    
    def test_default_optional(self):
        self.default_test('optional')
    
    def test_override_required(self):
        self.override_test('required')
    
    def test_override_optional(self):
        self.override_test('optional')
    
    def unlimited_default_test(self, parameter_name):
        method = self.get_method('unlimited', True)
        method(iovalue=[object()], **{parameter_name: []})
    
    def test_unlimited_required(self):
        self.unlimited_default_test('required')
    
    def test_unlimited_optional(self):
        self.unlimited_default_test('optional')

class TestIOProcessorStashDefaultsVerify(
    StashDefaultsVerifyTest,
    IOProcessorStashDefaultsTestCase,
    ):
    operation_name = 'verify'

class IOManagerStashDefaultsVerifyTestCase(IOManagerStashDefaultsTestCase):
    operation_name = 'verify'

class TestIOManagerStashDefaultsVerifyInput(
    StashDefaultsVerifyTest,
    IOManagerStashDefaultsVerifyTestCase,
    ):
    phase_name = 'input'

class TestIOManagerStashDefaultsVerifyOutput(
    StashDefaultsVerifyTest,
    IOManagerStashDefaultsVerifyTestCase,
    ):
    phase_name = 'output'

class StashDefaultsCoerceTest(object):
    def default_test(self, parameter_name):
        method = self.get_method(parameter_name)
        result = method(iovalue=BeforeCoercionType())
        assert isinstance(result, YesCoercionType)
    
    def override_test(self, parameter_name):
        initial_value = object()
        method = self.get_method(parameter_name)
        result = method(iovalue=initial_value, **{parameter_name: object})
        assert result is initial_value
    
    def test_default_required(self):
        self.default_test('required')
    
    def test_default_optional(self):
        self.default_test('optional')
    
    def test_override_required(self):
        self.override_test('required')
    
    def test_override_optional(self):
        self.override_test('optional')

class TestIOProcessorStashDefaultsCoerce(
    StashDefaultsCoerceTest,
    IOProcessorStashDefaultsTestCase,
    ):
    operation_name = 'coerce'
    
    def get_method(self, parameter_name):
        return IOProcessorStashDefaultsTestCase.get_method(
            self,
            parameter_name,
            YesCoercionType,
            coercion_functions={YesCoercionType: coerce_custom}
            )

class IOManagerStashDefaultsCoerceTestCase(IOManagerStashDefaultsTestCase):
    operation_name = 'coerce'
    
    def get_method(self, parameter_name):
        return IOManagerStashDefaultsTestCase.get_method(
            self,
            parameter_name,
            YesCoercionType,
            coercion_functions={YesCoercionType: coerce_custom}
            )

class TestIOManagerStashDefaultsCoerceInput(     
    StashDefaultsCoerceTest,
    IOManagerStashDefaultsCoerceTestCase,
    ):
    phase_name = 'input'

class TestIOManagerStashDefaultsCoerceOutput(     
    StashDefaultsCoerceTest,
    IOManagerStashDefaultsCoerceTestCase,
    ):
    phase_name = 'output'

# ----------------------- Subclass defaults tests ------------------------

@pytest.mark.b
class TestIOProcessorSubclassDefaults(unittest.TestCase):
    """ 'coercion_functions' and 'typecheck_functions' can be set as defaults
        in a subclass definition. """
    def typecheck_test(self, value, **kwargs):
        def reject_value(value, expected_type):
            raise TypeCheckFailureError
        class CustomIOProcessor(IOProcessor):
            typecheck_functions = {CustomType: reject_value}
        CustomIOProcessor(**kwargs).verify(iovalue=value)
    
    def test_typecheck_defaults(self):
        with pytest.raises(VerificationFailureError):
            self.typecheck_test(CustomType())
    
    def test_typecheck_init_overrides(self):
        self.typecheck_test(CustomType(), typecheck_functions={})
    
    def get_coercion_result(self, value, **kwargs):
        class CustomIOProcessor(IOProcessor):
            coercion_functions = {YesCoercionType: coerce_custom}
        return CustomIOProcessor(**kwargs).coerce(iovalue=value)
    
    def test_coercion_defaults(self):
        result = self.get_coercion_result(BeforeCoercionType())
        assert isinstance(result, YesCoercionType)
    
    def test_coercion_init_overrides(self):
        initial_value = BeforeCoercionType()
        result = self.get_coercion_result(initial_value, coercion_functions={})
        assert result is initial_value

@pytest.mark.a
class TestIOManagerSubclassDefaults(unittest.TestCase):
    """ '...coercion_functions' and '...typecheck_functions' can be set as
        defaults in a subclass definition. """
    def typecheck_test(self, value, phase_name, attr_part='', **kwargs):
        def reject_value(value, expected_type):
            raise TypeCheckFailureError
        
        class CustomIOManager(IOManager):
            pass
        
        attr_name = '_'.join(filter(None, [attr_part, 'typecheck_functions']))
        setattr(CustomIOManager, attr_name, {CustomType: reject_value})
        
        method_name = 'verify_' + phase_name
        manager = CustomIOManager(**kwargs)
        method = getattr(manager, method_name)
        
        method(iovalue=value)
    
    def typecheck_defaults_test(self, phase_name, *pargs, **kwargs):
        with pytest.raises(VerificationFailureError):
            self.typecheck_test(CustomType(), phase_name, *pargs, **kwargs)
    
    def typecheck_init_overrides_test(self, phase_name, *pargs, **kwargs):
        kwargs.update({'typecheck_functions': {}})
        self.typecheck_test(CustomType(), phase_name, *pargs, **kwargs)
    
    def test_typecheck_defaults_input(self):
        self.typecheck_defaults_test('input')
    
    def test_typecheck_defaults_output(self):
        self.typecheck_defaults_test('output')
    
    def test_typecheck_init_overrides_input(self):
        self.typecheck_init_overrides_test('input')
    
    def test_typecheck_init_overrides_output(self):
        self.typecheck_init_overrides_test('output')
    
    def test_typecheck_specific_defaults_input(self):
        self.typecheck_defaults_test('input', 'input')
    
    def test_typecheck_specific_defaults_output(self):
        self.typecheck_defaults_test('output', 'output')
    
    def test_typechcek_specific_init_overrides_input(self):
        self.typecheck_init_overrides_test('input', 'input')
    
    def test_typechcek_specific_init_overrides_output(self):
        self.typecheck_init_overrides_test('output', 'output')







