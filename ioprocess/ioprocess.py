""" Copyright (c) 2013 Josh Matthias <python.ioprocess@gmail.com> """

import datetime
import dateutil.parser
import decimal
import inspect
import uuid

""" Jargon:
    'ioval' --> 'Input/Output value'
    'tspec' --> 'Type specification dictionary'
    """

# --------------------------- Error classes ----------------------------

class Error(Exception):
    """ Base class for errors. """

class InvalidIOValuesError(Error):
    """ The 'iovals_dict' value submitted for processing did not conform to the
        provided 'tspec' values. """

class CoercionFailureResultError(Error):
    """ An 'ioval' value could not be coerced to the expected type.
        
        This error is used to pass a 'failure result', which is an instance of
        'WrongTypePair'. The failure result is used to generate human-readable
        output indicating why coercion failed. """
    def __init__(self, *pargs, **kwargs):
        self.failure_result = WrongTypePair(*pargs, **kwargs)

class CoercionFailureResultDictError(CoercionFailureResultError):
    """ Values in a dict or list of arguments could not be coerced to the
        expected type.
        
        This error is used to pass a 'failure result dictionary', a (possibly
        nested) dictionary of 'WrongTypePair' instances. """
    def __init__(self, failure_dict):
        self.failure_result = failure_dict

class TypeCheckFailureError(Error):
    pass

class TypeCheckSuccessError(Error):
    pass



# ----------------------- Custom parameter types -----------------------

class AnyType(object):
    """ A parameter that accept any data type. """

class ListOf(object):
    """ A list of items of a specified type.
        
        The specified type can be an tspec dictionary. """
    
    def __init__(self, tspec_obj):
        self.tspec_obj = tspec_obj
        
        type_name_self = type(self).__name__.strip("'").strip('"')
        if isinstance(tspec_obj, dict):
            type_name_obj = str(tspec_obj)
        else:
            type_name_obj = tspec_obj.__name__.strip("'").strip('"')
        
        self.__name__ = type_name_self + "({})".format(type_name_obj)
    
    def make_dict(self, length):
        return {i: self.tspec_obj for i in range(length)}
    
    def __repr__(self):
        return "{}({})".format(type(self).__name__, repr(self.tspec_obj))



# --------------------------- Useful things ----------------------------

class NotSet(object):
    """ Value when an argument or parameter is not given. """

class NoDifference(object):
    """ Return value when a 'difference' function returns no difference. """

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

def coerce_unicode_input(ioval):
    if not isinstance(ioval, str):
        return ioval
    
    return unicode(ioval)

def coerce_decimal_input(ioval):
    if not isinstance(ioval, int):
        return ioval
    
    return decimal.Decimal(ioval)

def coerce_uuid_input(ioval):
    if not isinstance(ioval, basestring):
        return ioval
    
    try:
        return uuid.UUID(ioval)
    except ValueError:
        pass
    
    return ioval

def coerce_datetime_input(ioval):
    if not isinstance(ioval, basestring):
        return ioval
    
    try:
        return dateutil.parser.parse(ioval)
    except ValueError:
        pass
    
    return ioval

default_coercion_functions_input = {
    unicode: coerce_unicode_input,
    decimal.Decimal: coerce_decimal_input,
    uuid.UUID: coerce_uuid_input,
    datetime.datetime: coerce_datetime_input,
    }

def coerce_uuid_output(ioval):
    if not isinstance(ioval, uuid.UUID):
        return ioval
    
    return str(ioval)

def coerce_datetime_output(ioval):
    if not isinstance(ioval, datetime.datetime):
        return ioval
    
    return ioval.isoformat()

default_coercion_functions_output = {
    uuid.UUID: coerce_uuid_output,
    datetime.datetime: coerce_datetime_output,
    }



# ----------------------------- Processor ------------------------------

class IOProcessor(object):
    def __init__(self, coercion_functions={}):
        self.coercion_functions = coercion_functions.copy()
    
    def process(
        self,
        iovals,
        required={},
        optional={},
        unlimited=False,
        ):
        iovals_dict = iovals.copy()
        required_tspec = required.copy()
        optional_tspec = optional.copy()
        
        combined_tspec = combine_tspecs(required_tspec, optional_tspec)
        
        missing = difference_dict(
            required_tspec,
            iovals_dict,
            comparison='missing',
            )
        if missing is NoDifference:
            missing = {}
        
        if unlimited:
            possibly_unknown_keys = (
                set(iovals_dict.keys()) & set(combined_tspec.keys())
                )
            possibly_unknown_iovals = {
                ikey: ivalue
                for ikey, ivalue
                in iovals_dict.items()
                if ikey in possibly_unknown_keys
                }
        else:
            possibly_unknown_iovals = iovals_dict
        
        unknown = difference_dict(
            possibly_unknown_iovals,
            combined_tspec,
            comparison='unknown',
            )
        if unknown is NoDifference:
            unknown = {}
        
        # Coerce input values
        try:
            result_dict = self.coerce_dict(iovals_dict, combined_tspec)
        except CoercionFailureResultError as exc:
            result_dict = None
            wrong_types = exc.failure_result
        else:
            wrong_types = {}
        
        if not (missing or unknown or wrong_types):
            return result_dict
        
        missing_output = make_missing_output(missing)
        
        err_msg_parts = [
            intro_part + str(output_part)
            for intro_part, output_part in
            [
                ('Missing: ', missing_output),
                ('Not allowed: ', unknown),
                ('Wrong type: ', wrong_types),
                ]
            if output_part
            ]
        
        err_msg = ('Invalid RPC arguments.\n' + '\n'.join(err_msg_parts))
        
        raise InvalidIOValuesError(err_msg)
    
    def coerce_ioval(self, ioval, expected_type, nonetype_ok=True):
        # Coerce container types.
        if isinstance(expected_type, dict):
            return self.coerce_dict(ioval, expected_type)
        
        if isinstance(expected_type, ListOf):
            return self.coerce_list(ioval, expected_type)
        
        # Coerce non-container types.
        if expected_type in self.coercion_functions:
            coercion_function = self.coercion_functions[expected_type]
            result = coercion_function(ioval)
        else:
            result = ioval
        
        # General case.
        if (
            isinstance(result, expected_type) or
            (expected_type is AnyType) or
            (result is None and nonetype_ok)
            ):
            return result
        
        raise CoercionFailureResultError(expected_type, ioval)
    
    def coerce_dict(self, iovals_dict, tspec, nonetype_ok=True):
        if not isinstance(iovals_dict, dict):
            raise CoercionFailureResultError(dict, iovals_dict)
        
        result_iovals = {}
        failure_dict = {}
        
        for key, arg_value in iovals_dict.items():
            if key not in tspec:
                result_iovals[key] = arg_value
                continue
            
            expected_type = tspec[key]
            
            try:
                result_iovals[key] = self.coerce_ioval(
                    arg_value,
                    expected_type,
                    nonetype_ok,
                    )
            except CoercionFailureResultError as exc:
                failure_dict[key] = exc.failure_result
        
        if failure_dict:
            raise CoercionFailureResultDictError(failure_dict)
        
        return result_iovals
    
    def coerce_list(self, arg_list, listof):
        if not isinstance(arg_list, list):
            raise CoercionFailureResultError(list, arg_list)
        
        iovals_dict = make_dict_from_list(arg_list)
        tspec = listof.make_dict(len(arg_list))
        
        result_dict = self.coerce_dict(
            iovals_dict,
            tspec,
            nonetype_ok=False,
            )
        
        result_list = [
            result_dict[ikey] for ikey in sorted(result_dict.keys())
            ]
        
        return result_list

def input_processor():
    return IOProcessor(coercion_functions=default_coercion_functions_input)

def output_processor():
    return IOProcessor(coercion_functions=default_coercion_functions_output)



# ----------------------------- Functions ------------------------------

def tspecs_from_callable(callable_obj):
    argspec = inspect.getargspec(callable_obj)
    
    parameters = list(argspec.args)
    
    if argspec.defaults is None:
        optionals_start = len(parameters)
    else:
        optionals_count = len(argspec.defaults)
        optionals_start = -1 * optionals_count
    
    required_list = parameters[:optionals_start]
    optional_list = parameters[optionals_start:]
    
    required_tspec = {ikey: AnyType for ikey in required_list}
    optional_tspec = {ikey: AnyType for ikey in optional_list}
    
    result = {
        'required': required_tspec,
        'optional': optional_tspec,
        }
    return result

def make_dict_from_list(list_obj):
    return dict(zip(range(len(list_obj)), list_obj))

def difference_item(item_a, item_b=NotSet, comparison=None):
    if comparison is None:
        raise TypeError("'comparison' is a required parameter.")
    
    if isinstance(item_a, dict):
        if isinstance(item_b, dict):
            return difference_dict(item_a, item_b, comparison)
        if comparison == 'unknown':
            if item_b is NotSet:
                return UnknownDict()
    elif isinstance(item_a, (list, ListOf)):
        if isinstance(item_b, (list, ListOf)):
            return difference_list(item_a, item_b, comparison)
        if comparison == 'unknown':
            if item_b is NotSet:
                return UnknownList()
    
    # 'item_a' is a type object or a builtin instance.
    
    if item_b is NotSet:
        return item_a
    
    return NoDifference

def difference_list(list_obj_a, list_obj_b, comparison):
    if isinstance(list_obj_a, list):
        dict_a = make_dict_from_list(list_obj_a)
        dict_b = list_obj_b.make_dict(len(list_obj_a))
    else:
        dict_a = list_obj_a.make_dict(len(list_obj_b))
        dict_b = make_dict_from_list(list_obj_b)
    
    return difference_dict(dict_a, dict_b, comparison)

def difference_dict(dict_a, dict_b, comparison):
    result = {}
    
    for ikey, item_a in dict_a.items():
        item_b = dict_b.get(ikey, NotSet)
        item_result = difference_item(item_a, item_b, comparison)
        if item_result is not NoDifference:
            result[ikey] = item_result
    
    if result:
        return result
    
    return NoDifference

def combine_tspecs(tspec_a, tspec_b):
    result = {}
    keys_a = set(tspec_a.keys())
    keys_b = set(tspec_b.keys())
    all_keys = keys_a | keys_b
    
    for key in keys_a & keys_b:
        if (
            isinstance(tspec_a[key], dict) and
            isinstance(tspec_b[key], dict)
            ):
            result[key] = combine_tspecs(tspec_a[key], tspec_b[key])
            all_keys.remove(key)
    
    for key in all_keys:
        result[key] = tspec_a.get(key, tspec_b.get(key))
    
    return result

def make_missing_output(missing_tspec):
    result = {}
    
    for key, value in missing_tspec.items():
        if isinstance(value, dict):
            result[key] = make_missing_output(value)
            continue
        
        result[key] = TypeNameRepresentation(value)
    
    return result






