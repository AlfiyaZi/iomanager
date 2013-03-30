""" Copyright (c) 2013 Josh Matthias <python.iomanager@gmail.com> """

import datetime
import dateutil.parser
import decimal
import inspect
import uuid

""" Jargon:
    'ioval' --> 'Input/Output value'
    'iospec' --> 'Input/Output specification dictionary'
    """

# --------------------------- Error classes ----------------------------

class Error(Exception):
    """ Base class for errors. """

class VerificationFailureError(Error):
    """ The 'iovals_dict' value submitted for processing did not conform to the
        provided 'iospec' values. """

class WrongTypeError(Error):
    """ An 'ioval' value could not be coerced to the expected type.
        
        This error is used to pass a 'failure result', which is an instance of
        'WrongTypePair'. The failure result is used to generate human-readable
        output indicating why coercion failed. """
    def __init__(self, *pargs, **kwargs):
        self.failure_result = WrongTypePair(*pargs, **kwargs)

class WrongTypeDictError(WrongTypeError):
    """ Values in a dict or list of arguments could not be coerced to the
        expected type.
        
        This error is used to pass a 'failure result dictionary', a (possibly
        nested) dictionary of 'WrongTypePair' instances. """
    def __init__(self, failure_dict):
        self.failure_result = failure_dict

class TypeCheckFailureError(Error):
    """ A value fails type confirmation.
        
        Raised by a custom 'typecheck' (type confirmation) function to force a
        value of the expected type to fail confirmation.
        
        Example: A function to reject subclasses of the expected type.
        
        def reject_subclasses(value, expected_type):
            if issubclass(type(value), expected_type):
                raise TypeCheckFailureError
            
            return value
        """

class TypeCheckSuccessError(Error):
    """ A value passes type confirmation.
        
        Raised by a custom 'typecheck' (type confirmation) function to allow
        a value not of the expected type to pass confirmation. """



# ----------------------- Custom parameter types -----------------------

class AnyType(object):
    """ A parameter that accept any data type. """

class ListOf(object):
    """ A list of items of a specified type.
        
        The specified type can be an iospec dictionary. """
    
    def __init__(self, iospec_obj):
        self.iospec_obj = iospec_obj
        
        type_name_self = type(self).__name__.strip("'").strip('"')
        if isinstance(iospec_obj, dict):
            type_name_obj = str(iospec_obj)
        else:
            type_name_obj = iospec_obj.__name__.strip("'").strip('"')
        
        self.__name__ = type_name_self + "({})".format(type_name_obj)
    
    def make_dict(self, length):
        return {i: self.iospec_obj for i in range(length)}
    
    def __repr__(self):
        return "{}({})".format(type(self).__name__, repr(self.iospec_obj))



# --------------------------- Useful things ----------------------------

class NotProvided(object):
    """ Value when an argument or parameter is not given. """

class NoDifference(object):
    """ Return value when a 'difference' function returns no difference.
        
        This is necessary so that 'difference_ioval', 'difference_dict' and
        'difference_list' can all return the same value. """

class UnknownDict(object):
    """ Used to generate succinct error messages when a not-allowed keyword
        argument has a dictionary value. """
    def __repr__(self):
        return '{...}'

class UnknownList(object):
    """ Like UnknownDict, but for lists. """
    def __repr__(self):
        return '[...]'

class WrongTypePair(object):
    """ Used to generate an error message for request arguments of the wrong
        type. """
    def __init__(self, type_obj, arg_value):
        self.pair = (type_obj, type(arg_value))
    
    def __repr__(self):
        type_names = [item.__name__ for item in self.pair]
        return "(expected '{}'; got '{}')".format(*type_names)

class TypeNameRepresentation(object):
    """ Used to generate error output. Replaces quotation marks arount type
        object .__name__ values. """
    def __init__(self, type_obj):
        self.type_name = type_obj.__name__
    
    def __repr__(self):
        result = self.type_name.strip("'").strip('"')
        result = '<{}>'.format(result)
        return result

def coerce_unicode_input(value):
    if not isinstance(value, str):
        return value
    
    return unicode(value)

def coerce_decimal_input(value):
    if not isinstance(value, int):
        return value
    
    return decimal.Decimal(value)

def coerce_uuid_input(value):
    if not isinstance(value, basestring):
        return value
    
    try:
        return uuid.UUID(value)
    except ValueError:
        pass
    
    return value

def coerce_datetime_input(value):
    if not isinstance(value, basestring):
        return value
    
    try:
        return dateutil.parser.parse(value)
    except ValueError:
        pass
    
    return value

default_input_coercion_functions = {
    unicode: coerce_unicode_input,
    decimal.Decimal: coerce_decimal_input,
    uuid.UUID: coerce_uuid_input,
    datetime.datetime: coerce_datetime_input,
    }

def coerce_uuid_output(value):
    if not isinstance(value, uuid.UUID):
        return value
    
    return str(value)

def coerce_datetime_output(value):
    if not isinstance(value, datetime.datetime):
        return value
    
    return value.isoformat()

default_output_coercion_functions = {
    uuid.UUID: coerce_uuid_output,
    datetime.datetime: coerce_datetime_output,
    }



# ----------------------------- Processor ------------------------------

class IOProcessor(object):
    def __init__(
        self,
        coercion_functions={},
        typecheck_functions={},
        ):
        self.coercion_functions = coercion_functions.copy()
        self.typecheck_functions = typecheck_functions.copy()
    
    def verify(
        self,
        iovals,
        required={},
        optional={},
        unlimited=False,
        ):
        iovals_dict = iovals.copy()
        required_iospec = required.copy()
        optional_iospec = optional.copy()
        
        combined_iospec = combine_iospecs(required_iospec, optional_iospec)
        
        missing = self.difference_dict(
            required_iospec,
            iovals_dict,
            )
        if missing is NoDifference:
            missing = {}
        
        if unlimited:
            """ When 'unlimited=True', only top-level keys are unlimited.
                Verification still occurs recursively for keys specified in the
                'combined_iospec'. """
            possibly_unknown_keys = (
                set(iovals_dict.keys()) & set(combined_iospec.keys())
                )
            possibly_unknown_iovals = {
                ikey: ivalue
                for ikey, ivalue
                in iovals_dict.items()
                if ikey in possibly_unknown_keys
                }
        else:
            possibly_unknown_iovals = iovals_dict
        
        unknown = self.difference_dict(
            possibly_unknown_iovals,
            combined_iospec,
            result_modifier=modify_unknown_result
            )
        if unknown is NoDifference:
            unknown = {}
        
        try:
            self.confirm_type_dict(iovals_dict, combined_iospec)
        except WrongTypeError as exc:
            wrong_types = exc.failure_result
        else:
            wrong_types = {}
        
        if not (missing or unknown or wrong_types):
            return
        
        missing_output = make_missing_output(missing)
        
        err_msg_parts = [
            caption_part + str(output_part)
            for caption_part, output_part in
            [
                ('Missing: ', missing_output),
                ('Not allowed: ', unknown),
                ('Wrong type: ', wrong_types),
                ]
            if output_part
            ]
        
        err_msg = ('Invalid RPC arguments.\n' + '\n'.join(err_msg_parts))
        
        raise VerificationFailureError(err_msg)

    def difference_ioval(
        self,
        item_a,
        item_b=NotProvided,
        result_modifier=None
        ):
        if all_are_instances((item_a, item_b), dict):
            return self.difference_dict(item_a, item_b, result_modifier)
        
        if all_are_instances((item_a, item_b), (list, ListOf)):
            return self.difference_list(item_a, item_b, result_modifier)
        
        if item_b is NotProvided:
            if result_modifier:
                return result_modifier(item_a)
            
            return item_a
        
        return NoDifference
    
    def difference_dict(self, dict_a, dict_b, *pargs, **kwargs):
        result = {}
        
        for ikey, item_a in dict_a.items():
            item_b = dict_b.get(ikey, NotProvided)
            item_result = (
                self.difference_ioval(item_a, item_b, *pargs, **kwargs)
                )
            if item_result is not NoDifference:
                result[ikey] = item_result
        
        if result:
            return result
        
        return NoDifference
    
    def difference_list(self, list_obj_a, list_obj_b, *pargs, **kwargs):
        if isinstance(list_obj_a, list):
            dict_a = make_dict_from_list(list_obj_a)
            dict_b = list_obj_b.make_dict(len(list_obj_a))
        else:
            dict_a = list_obj_a.make_dict(len(list_obj_b))
            dict_b = make_dict_from_list(list_obj_b)
        
        return self.difference_dict(dict_a, dict_b, *pargs, **kwargs)
    
    def confirm_type_ioval(self, ioval, expected_type, nonetype_ok=True):
        # Verify container types.
        if isinstance(expected_type, dict):
            self.confirm_type_dict(ioval, expected_type)
            return
        
        if isinstance(expected_type, ListOf):
            self.confirm_type_list(ioval, expected_type)
            return
        
        # Custom type-checking function.
        try:
            typecheck_function = self.typecheck_functions[expected_type]
        except KeyError:
            pass
        else:
            try:
                typecheck_function(ioval, expected_type)
            except TypeCheckSuccessError:
                return
            except TypeCheckFailureError:
                raise WrongTypeError(expected_type, ioval)
        
        # General case.
        if (
            isinstance(ioval, expected_type) or
            (expected_type is AnyType) or
            (ioval is None and nonetype_ok)
            ):
            return
        
        raise WrongTypeError(expected_type, ioval)
    
    def confirm_type_dict(self, iovals_dict, iospec, nonetype_ok=True):
        if not isinstance(iovals_dict, dict):
            raise WrongTypeError(dict, iovals_dict)
        
        wrong_types = {}
        
        for key, ioval in iovals_dict.items():
            if key not in iospec:
                continue
            
            expected_type = iospec[key]
            
            try:
                self.confirm_type_ioval(ioval, expected_type, nonetype_ok)
            except WrongTypeError as exc:
                wrong_types[key] = exc.failure_result
        
        if wrong_types:
            raise WrongTypeDictError(wrong_types)
    
    def confirm_type_list(self, iovals_list, listof):
        """ 'None' values are not permitted in lists.
            
            An attribute called 'lists_allow_none_values' is being considered
            to allow modification of this behavior. """
        if not isinstance(iovals_list, list):
            raise WrongTypeError(list, iovals_list)
        
        iovals_dict = make_dict_from_list(iovals_list)
        iospec = listof.make_dict(len(iovals_list))
        
        self.confirm_type_dict(iovals_dict, iospec, nonetype_ok=False)
    
    def coerce(
        self,
        iovals,
        required={},
        optional={},
        ):
        iovals_dict = iovals.copy()
        required_iospec = required.copy()
        optional_iospec = optional.copy()
        combined_iospec = combine_iospecs(required_iospec, optional_iospec)
        
        return self.coerce_dict(iovals_dict, combined_iospec)
    
    def coerce_ioval(self, ioval, expected_type, nonetype_ok=True):
        # Coerce container types.
        if isinstance(expected_type, dict):
            return self.coerce_dict(ioval, expected_type)
        
        if isinstance(expected_type, ListOf):
            return self.coerce_list(ioval, expected_type)
        
        # Coerce non-container types.
        try:
            coercion_function = self.coercion_functions[expected_type]
        except KeyError:
            result = ioval
        else:
            result = coercion_function(ioval)
        
        return result
    
    def coerce_dict(self, iovals_dict, iospec, nonetype_ok=True):
        result_iovals = {}
        
        for key, ioval in iovals_dict.items():
            try:
                expected_type = iospec[key]
            except KeyError:
                result_iovals[key] = ioval
                continue
            
            result_iovals[key] = self.coerce_ioval(ioval, expected_type)
        
        return result_iovals
    
    def coerce_list(self, iovals_list, listof):
        iovals_dict = make_dict_from_list(iovals_list)
        iospec = listof.make_dict(len(iovals_list))
        
        result_dict = self.coerce_dict(iovals_dict, iospec)
        
        result_list = [
            result_dict[ikey] for ikey in sorted(result_dict.keys())
            ]
        
        return result_list

class IOManager(object):
    def __init__(self, **kwargs):
        attr_names = [
            'coercion_functions',
            'input_coercion_functions',
            'output_coercion_functions',
            'typecheck_functions',
            'input_typecheck_functions',
            'output_typecheck_functions',
            ]
        
        attributes = {}
        
        for ikey, ivalue in kwargs.iteritems():
            if ikey not in attr_names:
                raise TypeError(
                    "__init__() got an unexpected keyword argument '{}'"
                    .format(ikey)
                    )
            attributes[ikey] = ivalue
        
        for attr_name, attr_value in attributes.iteritems():
            setattr(self, attr_name, attr_value)
    
    def make_ioprocessor(self, kind):
        """ coerce(), then verify(). """
        init_parts = {
            'coercion_functions': (
                '{}_coercion_functions'.format(kind),
                'coercion_functions'
                ),
            'typecheck_functions': (
                '{}_typecheck_functions'.format(kind),
                'typecheck_functions',
                ),
        }
        init_kwargs = {}
        for init_key, attr_names in init_parts.iteritems():
            for attr_name in attr_names:
                try:
                    init_kwargs[init_key] = getattr(self, attr_name)
                except AttributeError:
                    continue
                else:
                    break
        
        return IOProcessor(**init_kwargs)
    
    def process_input(
        self,
        iovals,
        required={},
        optional={},
        unlimited=False,
        ):
        """ coerce(), then verify(). """
        ioprocessor = self.make_ioprocessor('input')
        
        coerced_iovals = ioprocessor.coerce(iovals, required, optional)
        ioprocessor.verify(coerced_iovals, required, optional, unlimited)
        
        return coerced_iovals
    
    def process_output(
        self,
        iovals,
        required={},
        optional={},
        unlimited=False,
        ):
        """ verify(), then coerce(). """
        ioprocessor = self.make_ioprocessor('output')
        
        ioprocessor.verify(iovals, required, optional, unlimited)
        coerced_iovals = ioprocessor.coerce(iovals, required, optional)
        
        return coerced_iovals

def default_input_processor():
    return IOProcessor(coercion_functions=default_input_coercion_functions)

def default_output_processor():
    return IOProcessor(coercion_functions=default_output_coercion_functions)

def default_iomanager():
    return IOManager(
        input_coercion_functions=default_input_coercion_functions,
        output_coercion_functions=default_output_coercion_functions,
        )



# ----------------------------- Functions ------------------------------

def modify_unknown_result(ioval):
    if isinstance(ioval, dict):
        return UnknownDict()
    if isinstance(ioval, list):
        return UnknownList()
    
    return ioval

def iospecs_from_callable(callable_obj):
    argspec = inspect.getargspec(callable_obj)
    
    parameters = list(argspec.args)
    
    if argspec.defaults is None:
        optionals_start = len(parameters)
    else:
        optionals_count = len(argspec.defaults)
        optionals_start = -1 * optionals_count
    
    required_list = parameters[:optionals_start]
    optional_list = parameters[optionals_start:]
    
    required_iospec = {ikey: AnyType for ikey in required_list}
    optional_iospec = {ikey: AnyType for ikey in optional_list}
    
    result = {
        'required': required_iospec,
        'optional': optional_iospec,
        }
    return result

def make_dict_from_list(list_obj):
    return dict(zip(range(len(list_obj)), list_obj))

def all_are_instances(items, type_objs):
    if not isinstance(type_objs, tuple):
        type_objs = (type_objs, )
    
    for item in items:
        if not isinstance(item, type_objs):
            return False
    
    return True

def combine_iospecs(iospec_a, iospec_b):
    result = {}
    keys_a = set(iospec_a.keys())
    keys_b = set(iospec_b.keys())
    all_keys = keys_a | keys_b
    
    for key in keys_a & keys_b:
        if (
            isinstance(iospec_a[key], dict) and
            isinstance(iospec_b[key], dict)
            ):
            result[key] = combine_iospecs(iospec_a[key], iospec_b[key])
            all_keys.remove(key)
    
    for key in all_keys:
        result[key] = iospec_a.get(key, iospec_b.get(key))
    
    return result

def make_missing_output(missing_iospec):
    result = {}
    
    for key, value in missing_iospec.items():
        if isinstance(value, dict):
            result[key] = make_missing_output(value)
            continue
        
        result[key] = TypeNameRepresentation(value)
    
    return result






