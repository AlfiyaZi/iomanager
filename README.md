iomanager
=========

```iomanager``` is a tool for guaranteeing the structure and composition of input and
output from a Python program, with JSON in mind.

```iomanager``` has two main operations: verification, and coercion. On input, you
might perform coercion on the input data first (to make it suitable for internal
use), then verify data types and structure of the input data. On output, you might
verify the data types and structure of the output data first, then perform
coercion on the output data (to make it suitable for external use). Within
```iomanager```, the term 'process' indicates a combined verification-coercion
operation: 'process input' means 'coerce and then verify'; 'process output' means
'verify and then coerce'.

When an external program makes calls to a Python API, it is difficult to
distinguish between errors caused by faulty input data (bad structure, unusable
data types) and errors from within the API. ```iomanager``` inspects input data
and raises a single error, ```VerificationFailureError```, if faults are detected.
This error has a human-readable error message indicating the specific faults.
Applying the ```iomanager``` operations to output allows developers to write front
end code with certainty about API return values.

The coercion feature of ```iomanager``` makes it easier to pass data objects
through string-serialized formats like JSON. Instead of using a special convention
(like using JSON objects with a special '__type__' string value) and adding
special rules to the de-serialization operation, with ```iomanager``` you specify
exactly what data types are expected and ```iomanager``` attempts to coerce input
to the expected types. You can also specify custom functions for coercing each
data type, and you can specify different functions for input and output each. You
can specify custom functions for type-checking in the same way.

```iomanager``` makes it easier and faster for a developer to build a front end
which makes calls to a Python API, by giving clear error responses to the front
end developer. Using ```iomanager```, a developer can quickly determine whether an
exception has been caused by front-end code or back-end code. This is an important
consideration when building an API; a successful API will be used by multiple
front ends over time, and improving the front-end developer experience will lead
to more and better front ends, built more quickly.

Sample code
===========

```
import datetime
import json
import webob
from iomanager import IOManager, VerificationFailureError, ListOf

def api_method(a, b, c=False):
    """ Do something, return some value. """
    return_value = {
        'response_timestamp': datetime.datetime.utcnow(),
        'result': {
            'x': unicode(a.lower()),
            'y': sum(b)
            }
        }
    
    if c:
        return_value['result']['z'] = True
    
    return return_value

def coerce_datetime_output(value):
    try:
        return value.isoformat()
    except AttributeError:
        return value

def handle_request(request):
    manager = IOManager(
        input={
            'required': {'a': unicode, 'b': ListOf(int)},
            'optional': {'c': bool},
            },
        output={
            'required': {
                'response_timestamp': datetime.datetime,
                'result': {'x': unicode, 'y':int}
                },
            'optional': {
                'result': {'z': bool}
                },
            'coercion_functions': {datetime.datetime: coerce_datetime_output},
            }
        )
    
    input_values = json.loads(request.body)
    try:
        coerced_input_values = manager.process_input(iovalue=input_values)
    except VerificationFailureError as exc:
        return webob.Response(status=400, body=exc.error_msg)
    
    result_values = api_method(**coerced_input_values)
    
    try:
        coerced_result_values = manager.process_output(iovalue=result_values)
    except VerificationFailureError:
        return webob.Response(status=500, body=exc.error_msg)
    
    return webob.Response(status=200, body=json.dumps(coerced_result_values))
```

Verification - An example
=========================

Let's say you're building a web service. You have WebOB request object containing
some JSON-serialized input data, and you want to pass that input data to an API
method (a function). For this example, the API method returns the product of two
integers.

You're expecting the JSON document to decode to a dictionary whose keys correspond
to parameter names. You decode the JSON document and pass the result to your
function. 

```
import json
import webob

def api_method_multiply(x, y):
    """ Multiply two integers. Return an integer. """
    return x * y

def handle_request(request):
    input_values = json.loads(request.body)
    
    result = api_method(**input_values)
    response = webob.response(status=200, body=json.dumps(result))
    return response
```

A number of things can go wrong here. Let's assume JSON de-serialization passes
without exception. If ```input_values``` does not match up with the parameters of
```api_method```, a TypeError will be raised when 'api_method' is called. If one
of the values from ```input_values``` is of an unusable type, an error will
probably be raised somewhere within ```api_method```: it might be a
```TypeError```, an ```AttributeError```, or some custom error.

The problem is that there is no way to tell between an error raised by fault of
the input data and an error raised for some other reason. An error from
incorrectly-structured input would require a change to the front end; other
errors might require different input from the end-user, or might indicate a bug in
the back end code.

Here's how you would use ```iomanager``` in this situation. Before passing the
input data to your function, you would call the ```IOManager.verify_input```
method to guarantee the structure and composition of the input data. If
```verify_input``` encounters any problems with the input data (missing or unknown
parameter names, input values of the wrong type), a
```VerificationFailuereError``` is raised.

```
import webob
from iomanager import IOManager, VerificationFailureError

def api_method_multiply(x, y):
    """ Multiply two integers. Return an integer. """
    return x * y

def handle_request(request):
    input_values = json.loads(request.body)
    
    try:
        IOManager(input={'required': {'x': int, 'y': int}}).verify_input(
            iovalue=input_values
            )
    except VerificationFailureError as exc:
        return webob.response(status=400, body=exc.error_msg)
    
    result = api_method_multiply(**input_values)
    response = webob.response(status=200, body=json.dumps(result))
    return response
```

By using ```iomanager```, you can isolate errors caused by bad structure or
composition of input values, and issue an appropriate response. In the context of
a web service, this probably means a ```400 Bad Request``` HTTP status code.
Without ```iomanager```, a web service might issue a
```500 Internal Server Error``` HTTP status code in this situation. A ```500```
status would confuse the issue for a developer building a front end; should they
adjust their front end code, or should they report to the developer maintaining
the API? Using ```iomanager``` improves clarity in this situation.

Coercion - An example
=====================

In this case, let's say that your API method, called ```api_method_nextweek``,
takes in a date value and returns the date one week later (not a very useful
method, but this is just an example). Again, input is received in JSON-serialized
format.

JSON has no format for date values. The date value must be passed as a string, and
converted after input. This example uses the ```dateutil``` package, which is not
part of the python standard library, for parsing date strings. The reverse
operation is required before output; the resulting date value must be converted
back to a string before JSON serialization.

```
from datetime import timedelta
import dateutil.parser
import json
import webob

def api_method_nextweek(some_date):
    datetime_value = dateutil.parser.parse(some_date)
    next_week = some_date + timedelta(days=7)
    result_string = next_week.isoformat()
    return result_string

def handle_request(request):
    input_values = json.loads(request.body)
    result_value = api_method_nextweek(some_date=datetime_value)
    return webob.response(body=json.dumps(result_string))
```

Implementing this for each API method, and possibly for several argument values
for each method, results in a lot of repetitive code. ```iomanager``` makes it
possible to specify the data transformation ("coercion") operations for each data
type, for input and output.

```
import datetime
from datetime import timedelta
import dateutil.parser
import json
import webob
from iomanager import IOManager

def api_method_nextweek(some_date):
    return some_date + timedelta(days=7)

def coerce_datetime_input(value):
    if isinstance(value, basestring):
        try:
            return dateutil.parser.parse(value)
        except ValueError:
            pass
    
    return value

def coerce_datetime_output(value):
    try:
        value.isoformat()
    except AttributeError:
        return value

manager = IOManager(
    input={
        'required': {'some_date': datetime.datetime},
        'coercion_functions': {datetime.datetime: coerce_datetime_input}
        },
    output={
        'required': datetime.datetime,
        'coercion_functions': {datetime.datetime: coerce_datetime_output}
        },
    )

def handle_request(request):
    input_values = json.loads(request.body)
    coerced_input_values = manager.coerce_input(iovalue=input_values)
    
    result = api_method_nextweek(**coerced_input_values)
    
    coerced_result = manager.coerce_output(iovalue=result)
    return webob.response(body=json.dumps(coerced_result))
```

"But wait!" you're saying. "Using ```iomanager``` seems to require a lot more
code. Why would I want to use so much more code to accomplish the same thing?"

The answer is **consistency and reusability**. Without ```iomanager```, you must
include these transformations in each API function definition, for each parameter
that requires transformation. With ```iomanager```, you can specify your coercion
functions once, and re-use the same ```handle_request``` function for every API
function. There is a bit more to it of course; for an example of how
```iomanager``` can be used with a web framework, see
<a href=https://github.com/jmatthias/pyramid_apitree>pyramid_apitree</a>.

Also, since this use-case is so common, ```iomanager``` already includes this
coercion function! Here's the same example as above, but much shorter:

```
import datetime
from datetime import timedelta
import dateutil.parser
import json
import webob
import iomanager

def api_method_nextweek(some_date):
    return some_date + timedelta(days=7)

manager = iomanager.json_tools.io_manager(
    input={'required': {'some_date': datetime.datetime}},
    output={'required': datetime.datetime}
    )

def handle_request(request):
    input_values = json.loads(request.body)
    coerced_input_values = manager.coerce_input(iovalue=input_values)
    
    result = api_method_nextweek(**coerced_input_values)
    
    coerced_result = manager.coerce_output(iovalue=result)
    return webob.response(body=json.dumps(coerced_result))
```









