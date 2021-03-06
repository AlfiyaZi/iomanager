""" Copyright (c) 2013 Josh Matthias <python.iomanager@gmail.com> """

import inspect
from collections.abc import(
    Sequence,
    Mapping,
    )

""" Jargon:
    'ioval' --> 'Input/Output value'
    'iospec' --> 'Input/Output specification dictionary'
    """

# --------------------------- Error classes ----------------------------

class Error(Exception):
    """ Base class for errors. """

class VerificationFailureError(Error):
    """ The 'iovalue' value submitted for processing did not conform to the
        provided 'iospec' value. """
    def __init__(self, *pargs, **kwargs):
        if not pargs:
            pargs = ['Input/Output verification failed.']
        
        super(VerificationFailureError, self).__init__(*pargs, **kwargs)

class InputVerificationFailureError(VerificationFailureError):
    """ Raised by IOManager to indicate that verification has failed when
        'verify_input' was called. """

class OutputVerificationFailureError(VerificationFailureError):
    """ Raised by IOManager to indicate that verification has failed when
        'verify_output' was called. """

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

class CoercionSuccessError(Error):
    """ A value has been successfully coerced to the expected type.
        
        Raising this exception instead of simply returning the coerced value
        stops the coercion routine. This behavior can be used to 'stack'
        coercion functions. """



# ----------------------- Custom parameter types -----------------------

class AnyType(object):
    """ A parameter that accept any data type. """

class ListOf(object):
    """ A list of items of a specified type.
        
        The specified type can be an iospec dictionary. """
    
    def __init__(self, iospec_obj):
        self.iospec_obj = iospec_obj
        
        type_name_self = type(self).__name__.strip("'").strip('"')
        
        if is_container(iospec_obj, (Sequence, Mapping)):
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

class UnknownContainer(object):
    """ Used to generate succinct error messages when a not-allowed keyword
        argument has a container-type value.
            list --> '[...]'
            dict --> '{...}'
            etc.
        """
    def __init__(self, ioval):
        if not is_container(ioval, (Sequence, Mapping)):
            raise TypeError(
                "'ioval' must be a container object. Got: {}"
                .format(str(ioval))
                )
        self.representation = '...'.join(str(type(ioval)()))
    
    def __repr__(self):
        return self.representation

class WrongTypePair(object):
    """ Used to generate an error message for request arguments of the wrong
        type. """
    def __init__(self, type_obj, arg_value):
        self.pair = (type_obj, type(arg_value))
    
    def __repr__(self):
        type_names = []
        for item in self.pair:
            try:
                type_names.append(item.__name__)
            except AttributeError:
                type_names.append(type(item).__name__)
        
        return "(expected '{}'; got '{}')".format(*type_names)

class TypeNameRepresentation(object):
    """ Used to generate error output. Replaces quotation marks arount type
        object .__name__ values. """
    def __init__(self, type_obj):
        if type_obj is None:
            self.type_name = 'None'
        else:
            self.type_name = type_obj.__name__
    
    def __repr__(self):
        result = self.type_name.strip("'").strip('"')
        result = '<{}>'.format(result)
        return result



# ----------------------------- Processor ------------------------------

class IOProcessor(object):
    def __init__(
        self,
        required=NotProvided,
        optional=NotProvided,
        unlimited=False,
        typecheck_functions=NotProvided,
        coercion_functions=NotProvided,
        error_msg='Invalid input/output.'
        ):
        self.required = required
        self.optional = optional
        self.unlimited = unlimited
        self.error_msg = error_msg
        
        if typecheck_functions is not NotProvided:
            self.typecheck_functions = typecheck_functions.copy()
        if coercion_functions is not NotProvided:
            self.coercion_functions = coercion_functions.copy()
    
    def verify(self, iovalue):
        required, optional, unlimited = [
            getattr(self, attr_name)
            for attr_name in ['required', 'optional', 'unlimited']
            ]
        
        combined_iospec = combine_iospecs(required, optional)
        
        missing = self.difference_ioval(required, iovalue)
        unknown = self.difference_ioval(
            iovalue,
            combined_iospec,
            abbreviate=True,
            )
        
        if unlimited is True:
            unknown = self.filter_unlimited(unknown, combined_iospec)
        
        try:
            self.confirm_type_ioval(iovalue, combined_iospec)
        except WrongTypeError as exc:
            wrong_types = exc.failure_result
        else:
            wrong_types = None
        
        if (
            missing is NoDifference and
            unknown is NoDifference and
            wrong_types is None
            ):
            # Verification passes.
            return
        
        # Verification fails.
        err_msg_parts = [
            caption_part + str(output_part)
            for caption_part, output_part in
            [
                ('Missing: ', make_missing_output(missing)),
                ('Not allowed: ', unknown),
                ('Wrong type: ', wrong_types),
                ]
            if output_part and output_part is not NoDifference
            ]
        
        error_msg = '\n'.join([self.error_msg] + err_msg_parts)
        
        raise VerificationFailureError(error_msg)

    def difference_ioval(
        self,
        item_a,
        item_b=NotProvided,
        abbreviate=False,
        ):
        if all_are_containers((item_a, item_b), Mapping):
            return self.difference_dict(item_a, item_b, abbreviate)
        
        if all_are_containers((item_a, item_b), (Sequence, ListOf)):
            return self.difference_list(item_a, item_b, abbreviate)
        
        if item_b is NotProvided:
            if abbreviate:
                # For 'unknown' output. Abbreviate container results.
                try:
                    return UnknownContainer(item_a)
                except TypeError:
                    pass
            
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
    
    def difference_list(self, list_a, list_b, *pargs, **kwargs):
        """ The difference between two lists, or between a list and a
            ListOf. """
        for item in [list_a, list_b]:
            try:
                target_length = len(item)
                break
            except TypeError:
                continue
        else:
            raise TypeError(
                "At least one of 'list_a', 'list_b' must be an iterable. Got: "
                "list_a={}, list_b={}".format(list_a, list_b)
                )
        
        dict_a, dict_b = [
            make_dict_from_listlike(item, target_length)
            for item in [list_a, list_b]
            ]
        
        return self.difference_dict(dict_a, dict_b, *pargs, **kwargs)
    
    def filter_unlimited(self, unknown, combined_iospec):
        """ Take the 'unlimited' argument into account. Only keys in the
            intersection of 'unknown' and 'iospec_dict' are considered unknown
            when 'unlimited=True'.
            
            In other words, when unlimited=True, top-level keys (and only
            top-level keys) are unlimited."""
        if unknown is NoDifference:
            return NoDifference
        
        if is_container(combined_iospec, (Sequence, ListOf)):
            iospec_dict = make_dict_from_listlike(combined_iospec, len(unknown))
        else:
            iospec_dict = combined_iospec
        
        result = {
            ikey: ivalue for ikey, ivalue in unknown.items()
            if ikey in iospec_dict
            }
        
        if not result:
            return NoDifference
        return result
    
    def confirm_type_ioval(self, ioval, expected_type, nonetype_ok=True):
        if expected_type is NotProvided:
            expected_type = AnyType
        
        # Verify container types.
        if is_container(expected_type, Mapping):
            self.confirm_type_dict(ioval, expected_type)
            return
        
        if is_container(expected_type, (Sequence, ListOf)):
            self.confirm_type_list(ioval, expected_type)
            return
        
        # Custom type-checking function.
        try:
            typecheck_function = self.typecheck_functions[expected_type]
        except (KeyError, AttributeError):
            pass
        else:
            try:
                typecheck_function(ioval, expected_type)
            except TypeCheckSuccessError:
                return
            except TypeCheckFailureError:
                raise WrongTypeError(expected_type, ioval)
        
        # Catch 'None' values.
        if ioval is None and not nonetype_ok:
            raise WrongTypeError(expected_type, ioval)
        
        # General case.
        if (
            isinstance(ioval, expected_type) or
            (expected_type is AnyType) or
            (ioval is None and nonetype_ok)
            ):
            return
        
        raise WrongTypeError(expected_type, ioval)
    
    def confirm_type_dict(self, iovals_dict, iospec_dict, nonetype_ok=True):
        if not isinstance(iovals_dict, Mapping):
            raise WrongTypeError(dict, iovals_dict)
        
        wrong_types = {}
        
        for key, ioval in iovals_dict.items():
            if key not in iospec_dict:
                continue
            
            expected_type = iospec_dict[key]
            
            try:
                self.confirm_type_ioval(ioval, expected_type, nonetype_ok)
            except WrongTypeError as exc:
                wrong_types[key] = exc.failure_result
        
        if wrong_types:
            raise WrongTypeDictError(wrong_types)
    
    def confirm_type_list(self, iovals_list, iospec_obj):
        """ 'None' values are not permitted when ListOf is expected.
            
            An attribute called 'lists_allow_none_values' is being considered
            to allow modification of this behavior. """
        if not is_container(iovals_list, Sequence):
            raise WrongTypeError(iospec_obj, iovals_list)
        
        iovals_dict = make_dict_from_listlike(iovals_list)
        
        iospec = make_dict_from_listlike(iospec_obj, len(iovals_list))
        
        nonetype_ok = not isinstance(iospec_obj, ListOf)
        
        self.confirm_type_dict(iovals_dict, iospec, nonetype_ok=nonetype_ok)
    
    def coerce(self, iovalue):
        required, optional = [
            getattr(self, attr_name)
            for attr_name in ['required', 'optional']
            ]
        
        combined_iospec = combine_iospecs(required, optional)
        
        return self.coerce_ioval(iovalue, combined_iospec)
    
    def coerce_ioval(self, ioval, expected_type, nonetype_ok=True):
        # Coerce container types.
        if is_container(expected_type, Mapping):
            return self.coerce_dict(ioval, expected_type)
        
        if is_container(expected_type, (Sequence, ListOf)):
            return self.coerce_list(ioval, expected_type)
        
        # Coerce non-container types.
        try:
            coercion_function = self.coercion_functions[expected_type]
        except (KeyError, AttributeError):
            return ioval
        
        try:
            return coercion_function(ioval, expected_type)
        except CoercionSuccessError as exc:
            return exc.args[0]
    
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
    
    def coerce_list(self, iovals_list, iospec_obj):
        iovals_dict = make_dict_from_listlike(iovals_list)
        
        iospec = make_dict_from_listlike(iospec_obj, len(iovals_list))
        
        result_dict = self.coerce_dict(iovals_dict, iospec)
        
        result_list = [
            result_dict[ikey] for ikey in sorted(result_dict.keys())
            ]
        
        return result_list

class IOManager(object):
    def __init__(
        self,
        input_kwargs={},
        output_kwargs={},
        typecheck_functions=NotProvided,
        coercion_functions=NotProvided,
        ):
        # Lowest precedence - General defaults from (sub)class attributes.
        default_general_kwargs = {
            ikey: getattr(self, ikey, NotProvided)
            for ikey in ['typecheck_functions', 'coercion_functions']
            }
        
        # Next precedence - Specific defaults from (sub)class attributes.
        default_input_kwargs, default_output_kwargs = [
            getattr(self, ikey, {})
            for ikey in ['input_kwargs', 'output_kwargs']
            ]
        
        # Next precedence - General kwargs from constructor arguments.
        general_kwargs = {
            ikey: ivalue
            for ikey, ivalue in [
                ('typecheck_functions', typecheck_functions),
                ('coercion_functions', coercion_functions),
                ]
            if ivalue is not NotProvided
            }
        
        # Start with the lowest precedence, update with higher-precedence.
        total_input_kwargs, total_output_kwargs = [
            default_general_kwargs.copy() for i in range(2)
            ]
        
        total_input_kwargs.update(default_input_kwargs)
        total_output_kwargs.update(default_output_kwargs)
        
        for ikwargs in [total_input_kwargs, total_output_kwargs]:
            ikwargs.update(general_kwargs)
        
        # Highest precedence - specific kwargs from constructor arguments.
        total_input_kwargs.update(input_kwargs)
        total_output_kwargs.update(output_kwargs)
        
        self.input_processor = IOProcessor(
            error_msg='Invalid input.',
            **total_input_kwargs
            )
        self.output_processor = IOProcessor(
            error_msg='Invalid output.',
            **total_output_kwargs
            )
    
    def process_input(self, iovalue):
        """ coerce(), then verify(). """
        coerced_iovalue = self.coerce_input(iovalue)
        self.verify_input(coerced_iovalue)
        
        return coerced_iovalue
    
    def process_output(self, iovalue):
        """ verify(), then coerce(). """
        self.verify_output(iovalue)
        coerced_iovalue = self.coerce_output(iovalue)
        
        return coerced_iovalue
    
    def coerce_input(self, *pargs, **kwargs):
        return self.input_processor.coerce(*pargs, **kwargs)
    
    def coerce_output(self, *pargs, **kwargs):
        return self.output_processor.coerce(*pargs, **kwargs)
    
    def verify_input(self, *pargs, **kwargs):
        try:
            return self.input_processor.verify(*pargs, **kwargs)
        except VerificationFailureError as exc:
            raise InputVerificationFailureError(*exc.args)
    
    def verify_output(self, *pargs, **kwargs):
        try:
            return self.output_processor.verify(*pargs, **kwargs)
        except VerificationFailureError as exc:
            raise OutputVerificationFailureError(*exc.args)



# ----------------------------- Functions ------------------------------

def is_container(obj, classinfo):
    """ 'obj' is an instance of 'classinfo', but is not a 'str' or 'bytes'
        instance. """
    if isinstance(obj, classinfo) and not isinstance(obj, (str, bytes)):
        return True
    return False

def all_are_containers(objs, classinfo):
    for item in objs:
        if not is_container(item, classinfo):
            return False
    
    return True

def iospecs_from_callable(callable_obj):
    if not hasattr(callable_obj, '__call__'):
        raise TypeError(
            "{} is not callable.".format(type(callable_obj).__name__)
        )
    if inspect.isfunction(callable_obj):
        argspec = inspect.getargspec(callable_obj)
        parameters = list(argspec.args)
    else:
        argspec = inspect.getargspec(callable_obj.__call__)
        # Get rid of the 'self' parameter.
        parameters = list(argspec.args)[1:]
    
    defaults = argspec.defaults
    
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

def make_dict_from_listlike(listlike_obj, target_length=None):
    """ Make a dictionary from an iterable or a ListOf instance.
        
        'target_length' is only used if the listlike_obj is a ListOf
        instance. """
    if isinstance(listlike_obj, ListOf):
        if target_length is None:
            raise TypeError(
                "'target_length' must be provided when 'listlike_obj' is a "
                "'ListOf' instance."
                )
        return listlike_obj.make_dict(target_length)
    
    return dict(zip(range(len(listlike_obj)), listlike_obj))

def combine_iospecs(iospec_a=NotProvided, iospec_b=NotProvided):
    if all_are_containers((iospec_a, iospec_b), dict):
        return combine_iospecs_dict(iospec_a, iospec_b)
    
    if all_are_containers((iospec_a, iospec_b), Sequence):
        return combine_iospecs_list(iospec_a, iospec_b)
    
    if iospec_a is NotProvided:
        if iospec_b is NotProvided:
            return AnyType
        return iospec_b
    return iospec_a

def combine_iospecs_dict(iospec_a, iospec_b):
    all_keys = set(iospec_a.keys()) | set(iospec_b.keys())
    
    return {
        ikey: combine_iospecs(
            iospec_a.get(ikey, NotProvided),
            iospec_b.get(ikey, NotProvided),
            )
        for ikey in all_keys
        }

def combine_iospecs_list(iospec_list_a, iospec_list_b):
    iospec_a = make_dict_from_listlike(iospec_list_a)
    iospec_b = make_dict_from_listlike(iospec_list_b)
    
    result_dict = combine_iospecs_dict(iospec_a, iospec_b)
    
    return [result_dict[i] for i in sorted(result_dict.keys())]

def make_missing_output(iospec):
    if iospec is NoDifference:
        return None
    
    if is_container(iospec, Mapping):
        return make_missing_output_dict(iospec)
    
    return TypeNameRepresentation(iospec)

def make_missing_output_dict(iospec):
    return {
        ikey: make_missing_output(ivalue)
        for ikey, ivalue in iospec.items()
        }






