'''
This module implements a JSON 1.0 compatible dispatcher

see http://json-rpc.org/wiki/specification
'''
from types import StringTypes
from .exceptions import RpcException, BadDataException, BadMethodException
from django.utils import simplejson as json


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
                'message': error.message,
                'code': error.code,
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
                'name': 'JSONRPCError',
                'exception': 'RpcException',
                'message': 'Failed to encode return value',
                'code': 100,
            }
            result = {
                'id': api_call_id,
                'result': None,
                'error': error
            }
            return json.dumps(result, indent=self.JSON_INDENT, cls=self.json_encoder)


    def encode_error(self, error):
        assert isinstance(error, RpcException)
        return self._encode_result(error.api_call_id, error=error)


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
            raise BadDataException('JSON must contain attributes method and params', api_call_id=api_call_id)

        if not isinstance(jsondict['method'], StringTypes):
            raise BadMethodException('JSON Wrong parameter method', api_call_id=api_call_id)

        if not isinstance(jsondict['params'], list):
            raise BadMethodException('JSON method params has to be Array', api_call_id=api_call_id)

        if jsondict['method'] not in self.methods:
            raise BadMethodException('Called method %s does not exist in this api, see system.listMethods' % jsondict['method'], api_call_id=api_call_id)

        result = self.methods[jsondict.get('method')](*jsondict.get('params'), **kwargs)
        return self._encode_result(api_call_id, result=result)

