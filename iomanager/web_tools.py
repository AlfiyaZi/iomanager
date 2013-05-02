import datetime
import dateutil.parser
import decimal
import uuid
from .iomanager import (
    IOProcessor,
    IOManager,
    CoercionSuccessError,
    )

def coerce_bool_input(value, expected_type):
    if not isinstance(value, str):
        return value
    
    bool_values = {
        'true': True,
        'false': False,
        }
    
    try:
        result = bool_values[value.lower()]
    except KeyError:
        return value
    else:
        raise CoercionSuccessError(result)

def coerce_numeric_input(value, expected_type):
    if not isinstance(value, str):
        return value
    
    try:
        result = expected_type(value)
    except ValueError:
        return value
    else:
        raise CoercionSuccessError(result)

def coerce_decimal_input(value, expected_type):
    if not isinstance(value, (str, int)):
        return value
    
    try:
        result = decimal.Decimal(value)
    except ArithmeticError:
        return value
    else:
        raise CoercionSuccessError(result)

def coerce_uuid_input(value, expected_type):
    if not isinstance(value, str):
        return value
    
    try:
        result = uuid.UUID(value)
    except ValueError:
        return value
    else:
        raise CoercionSuccessError(result)

def coerce_datetime_input(value, expected_type):
    if not isinstance(value, str):
        return value
    
    try:
        result = dateutil.parser.parse(value)
    except ValueError:
        return value
    else:
        raise CoercionSuccessError(result)

input_coercion_functions = {
    bool: coerce_bool_input,
    int: coerce_numeric_input,
    float: coerce_numeric_input,
    decimal.Decimal: coerce_decimal_input,
    uuid.UUID: coerce_uuid_input,
    datetime.datetime: coerce_datetime_input,
    }

def coerce_uuid_output(value, expected_type):
    if not isinstance(value, uuid.UUID):
        return value
    
    return str(value)

def coerce_datetime_output(value, expected_type):
    if not isinstance(value, datetime.datetime):
        return value
    
    return value.isoformat()

output_coercion_functions = {
    uuid.UUID: coerce_uuid_output,
    datetime.datetime: coerce_datetime_output,
    }

def input_processor(**kwargs):
    kwargs.setdefault('coercion_functions', input_coercion_functions)
    return IOProcessor(**kwargs)

def output_processor(**kwargs):
    kwargs.setdefault('coercion_functions', output_coercion_functions)
    return IOProcessor(**kwargs)

class WebIOManager(IOManager):
    input_kwargs={'coercion_functions': input_coercion_functions}
    output_kwargs={'coercion_functions': output_coercion_functions}