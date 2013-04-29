import pytest
import unittest
import datetime
import uuid
import decimal
import iomanager

class TypeCoercionDefaultFunctionsTest(unittest.TestCase):
    """ Confirm that the default type coercion functions behave as expected. """
    class ArbitraryType(object):
        """ This class is used to test a coercion function's effect upon an
            arbitrarily-typed value. """
    
    def coercion_test(self, type_obj, value, expected):
        coercion_function = self.coercion_functions[type_obj]
        
        result = coercion_function(value, type_obj)
        assert result == expected
    
    def arbitrary_value_test(self, type_obj):
        class ArbitraryType(object):
            """ An arbitrary type which should pass through coercion
                unchanged. """
        arbitrary_value = self.ArbitraryType()
        self.coercion_test(type_obj, arbitrary_value, arbitrary_value)

class TestTypeCoercionDefaultFunctionsInput(TypeCoercionDefaultFunctionsTest):
    """ Confirm that input values coerce correctly. """
    coercion_functions = iomanager.web_tools.input_coercion_functions
    
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
    coercion_functions = iomanager.web_tools.output_coercion_functions
    
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
        iospec =  {'value': type_obj}
        
        output_processor = iomanager.web_tools.output_processor(
            required=iospec,
            )
        input_processor = iomanager.web_tools.input_processor(
            required=iospec,
            )
        
        output_result = output_processor.coerce(
            iovalue={'value': starting_value},
            )
        
        final_result = input_processor.coerce(
            iovalue=output_result,
            )
        
        final_value = final_result['value']
        
        assert final_value == starting_value
    
    def test_datetime(self):
        dt_value = datetime.datetime.utcnow()
        self.coercion_cycle_test(datetime.datetime, dt_value)
    
    def test_uuid(self):
        uuid_value = uuid.uuid4()
        self.coercion_cycle_test(uuid.UUID, uuid_value)