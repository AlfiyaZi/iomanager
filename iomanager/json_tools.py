import datetime
import dateutil.parser
import decimal
import uuid
from .iomanager import IOProcessor, IOManager

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

input_coercion_functions = {
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

def io_manager():
    return IOManager(
        input_coercion_functions=input_coercion_functions,
        output_coercion_functions=output_coercion_functions,
        )