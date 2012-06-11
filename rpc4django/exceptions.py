
class RpcException(Exception):
    """
    General exception for rpc.

    Is exported as:
    {
        'error': {
            'message': self.message,
            'code': self.code,
            'name': self.__class__.__name__
        }
    }
    """
    code = 100

class BadDataException(RpcException):
    """
    Something is wrong with data - missing, not a JSON, not a dict
    """
    code = 101

class BadMethodException(RpcException):
    """
    Exception raised when user data are wrong about called method - missing method name, wrong name, ..
    """
    code = 102

class UnknownProcessingError(RpcException):
    """
    When api methods throws an exception which is not inherited from ProcessingError
    """
    code = 104

class ProcessingException(RpcException):
    """
    Exception for use in api methods.

    For overriding the code attribute.
    """
    code = 200

class BadParamsException(ProcessingException):
    """
    This exception should be raised when method gets wrong params.
    """
    code = 201