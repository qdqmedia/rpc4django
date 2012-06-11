'''
This module implements a JSON 1.0 compatible dispatcher

see http://json-rpc.org/wiki/specification
'''
from django.conf import settings
import traceback
from types import StringTypes
from .exceptions import RpcException, UnknownProcessingError, BadDataException, BadMethodException

# attempt to import json from 3 sources:
# 1. try to import it from django
# 2. if this is not run through django, try to import the simplejson module
# 3. import the json module that is only present in python >= 2.6
try:
    from django.utils import simplejson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json


class JSONRPCDispatcher:
    '''
    This class can be used encode and decode jsonrpc messages, dispatch
    the requested method with the passed parameters, and return any response
    or error.
    '''

    # indent the json output by this many characters
    # 0 does newlines only and None does most compact
    # This is consistent with SimpleXMLRPCServer output
    JSON_INDENT = 4
    
    def __init__(self, json_encoder=None):
        self.json_encoder = json_encoder
        self.methods = {}
    
    def register_function(self, method, external_name):
        '''
        Registers a method with the jsonrpc dispatcher.
        
        This method can be called later via the dispatch method.
        '''
        self.methods[external_name] = method


    def _encode_result(self, api_call_id, result=None, error=None):
        assert error is None or isinstance(error, RpcException)
        assert not (result and error)
        if error:
            error = {
                'name': 'JSONRPCError',
                'exception': error.__class__.__name__,
                'code': error.code,
                'message': error.message
            }
        result = {
            'id': api_call_id,
            'result': result,
            'error': error
        }
        try:
            return json.dumps(result, indent=self.JSON_INDENT, cls=self.json_encoder)
        except:
            error = {
                'message': 'Failed to encode return value',
                'code': 100,
                'name': 'JSONRPCError',
                'exception': 'RpcException'
            }
            result = {
                'id': api_call_id,
                'result': None,
                'error': error
            }
            return json.dumps(result, indent=self.JSON_INDENT, cls=self.json_encoder)


    def dispatch(self, json_data, **kwargs):
        '''
        Verifies that the passed json encoded string
        is in the correct form according to the json-rpc spec
        and calls the appropriate Python method

        **Checks**

         1. that the string encodes into a javascript Object (dictionary)
         2. that 'method' and 'params' are present
         3. 'method' must be a javascript String type
         4. 'params' must be a javascript Array type

        Returns the JSON encoded response
        '''
        api_call_id = ''
        try:

            if not json_data:
                raise BadDataException('No POST data')

            try:
                # attempt to do a json decode on the data
                jsondict = json.loads(json_data)
            except ValueError:
                raise BadDataException('JSON decoding error')

            if not isinstance(jsondict, dict):
                # verify the json data was a javascript Object which gets decoded
                # into a python dictionary
                raise BadDataException('JSON does not contain dict as its root object')

            api_call_id = jsondict.get('id', '')

            if not 'method' in jsondict or not 'params' in jsondict:
                # verify the dictionary contains the correct keys
                # for a proper jsonrpc call
                raise BadDataException('JSON must contain attributes method and params')

            if not isinstance(jsondict['method'], StringTypes):
                raise BadMethodException('JSON Wrong parameter method')

            if not isinstance(jsondict['params'], list):
                raise BadMethodException('JSON method params has to be Array')

            if jsondict['method'] not in self.methods:
                raise BadMethodException('Called method %s does not exist in this api, see system.listMethods' % jsondict['method'])

            result = self.methods[jsondict.get('method')](*jsondict.get('params'), **kwargs)
            return self._encode_result(api_call_id, result=result)

        except RpcException as e:
            if settings.DEBUG:
                traceback.print_exc()
            return self._encode_result(api_call_id, error=e)
        except Exception as e:
            traceback.print_exc()
            return self._encode_result(api_call_id, error=UnknownProcessingError('%s: %s' % (e.__class__.__name__, e.message)))
