import pytest
import unittest
import datetime
import uuid
import decimal
import iomanager

pytestmark = pytest.mark.a

class TypeCoercionDefaultFunctionsTest(unittest.TestCase):
    """ Confirm that the default type coercion functions behave as expected. """
    class ArbitraryType(object):
        """ This class is used to test a coercion function's effect upon an
            arbitrarily-typed value. """
    
    def coercion_test(self, type_obj, value, expected):
        processor = iomanager.IOProcessor(
            required=type_obj,
            coercion_functions=self.coercion_functions,
            )
        
        result = processor.coerce(value)
        
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
    
    def test_datetime_gets_arbitrary_type(self):
        self.arbitrary_value_test(datetime.datetime)
    
    def test_uuid_gets_arbitrary_type(self):
        self.arbitrary_value_test(uuid.UUID)
    
    def test_bool_gets_arbitrary_type(self):
        self.arbitrary_value_test(bool)
    
    def test_int_gets_arbitrary_type(self):
        self.arbitrary_value_test(int)
    
    def test_float_gets_arbitrary_type(self):
        self.arbitrary_value_test(float)
    
    def test_decimal_gets_arbitrary_type(self):
        self.arbitrary_value_test(decimal.Decimal)
    
    # --------------------- Coercion result tests ----------------------
    
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
    
    def invalid_string_test(self, expected_type, invalid_string='xxx'):
        self.coercion_test(
            expected_type,
            value=invalid_string,
            expected=invalid_string,
            )
    
    def bool_string_test(self, bool_string, expected):
        self.coercion_test(
            bool,
            value=bool_string,
            expected=expected,
            )
    
    def test_bool_gets_true_string(self):
        self.bool_string_test('true', True)
    
    def test_bool_gets_false_string(self):
        self.bool_string_test('false', False)
    
    def test_bool_gets_invalid_string(self):
        self.invalid_string_test(bool)
    
    def test_int_gets_string(self):
        self.coercion_test(
            int,
            value='123',
            expected=123
            )
    
    def test_int_gets_invalid_string(self):
        self.invalid_string_test(int)
    
    def test_float_gets_string(self):
        self.coercion_test(
            float,
            value='123.456',
            expected=123.456,
            )
    
    def test_float_gets_invalid_string(self):
        self.invalid_string_test(float)
    
    def test_decimal_gets_string(self):
        decimal_value = decimal.Decimal('123.456')
        self.coercion_test(
            decimal.Decimal,
            value=str(decimal_value),
            expected=decimal_value,
            )
    
    def test_decimal_gets_invalid_string(self):
        self.invalid_string_test(decimal.Decimal)
    
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