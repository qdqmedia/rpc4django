'''
The main entry point for RPC4Django. Usually, the user simply puts
:meth:`serve_rpc_request <rpc4django.views.serve_rpc_request>` into ``urls.py``

::

    urlpatterns = patterns('',
        # rpc4django will need to be in your Python path
        (r'^RPC2$', 'rpc4django.views.serve_rpc_request'),
    )

'''

import logging
import traceback
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch, get_mod_func
from django.utils.importlib import import_module
from .exceptions import UnknownProcessingError, RpcException, BadDataException
from rpcdispatcher import RPCDispatcher
from jsonrpcdispatcher import json
from __init__ import version

logger = logging.getLogger('rpc4django')

# these restrictions can change the functionality of rpc4django
# but they are completely optional
# see the rpc4django documentation for more details
LOG_REQUESTS_RESPONSES = getattr(settings, 'RPC4DJANGO_LOG_REQUESTS_RESPONSES', True)
RESTRICT_INTROSPECTION = getattr(settings, 'RPC4DJANGO_RESTRICT_INTROSPECTION', False)
RESTRICT_OOTB_AUTH = getattr(settings, 'RPC4DJANGO_RESTRICT_OOTB_AUTH', True)
RESTRICT_JSON = getattr(settings, 'RPC4DJANGO_RESTRICT_JSONRPC', False)
RESTRICT_METHOD_SUMMARY = getattr(settings, 'RPC4DJANGO_RESTRICT_METHOD_SUMMARY', False)
RESTRICT_RPCTEST = getattr(settings, 'RPC4DJANGO_RESTRICT_RPCTEST', False)
RESTRICT_RPCTEST = getattr(settings, 'RPC4DJANGO_RESTRICT_RPCTEST', False)
HTTP_ACCESS_CREDENTIALS = getattr(settings, 'RPC4DJANGO_HTTP_ACCESS_CREDENTIALS', False)
HTTP_ACCESS_ALLOW_ORIGIN = getattr(settings, 'RPC4DJANGO_HTTP_ACCESS_ALLOW_ORIGIN', '')
JSON_ENCODER = getattr(settings, 'RPC4DJANGO_JSON_ENCODER', 'django.core.serializers.json.DjangoJSONEncoder')

# get a list of the installed django applications
# these will be scanned for @rpcmethod decorators
APPS = getattr(settings, 'INSTALLED_APPS', [])


def serve_rpc_request(request):
    '''
    Handles rpc calls based on the content type of the request or
    returns the method documentation page if the request
    was a GET.

    **Parameters**

    ``request``
        the Django HttpRequest object

    '''
    if request.method == "POST":
        # Handle POST request with RPC payload

        if LOG_REQUESTS_RESPONSES:
            logger.debug('Incoming request: %s' %str(request.raw_post_data))

        # From now on only JSON
        protocol = dispatcher.jsonrpcdispatcher
        response_type = 'application/json'

        try:

            if response_type not in request.META.get('CONTENT_TYPE'):
                raise BadDataException('Use %s content type' % response_type)

            dispatcher.check_request_permission(request)
            response = protocol.dispatch(request.raw_post_data, request=request)

        except RpcException as e:

            if settings.DEBUG:
                traceback.print_exc()
            response =  protocol.encode_error(e)

        except Exception as e:

            traceback.print_exc()
            response =  protocol.encode_error(UnknownProcessingError('%s: %s' % (e.__class__.__name__, e.message)))

        return HttpResponse(response, response_type)

    elif request.method == 'OPTIONS':
        # Handle OPTIONS request for "preflighted" requests
        # see https://developer.mozilla.org/en/HTTP_access_control

        response = HttpResponse('', 'text/plain')

        origin = request.META.get('HTTP_ORIGIN', 'unknown origin')
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Max-Age'] = 0
        response['Access-Control-Allow-Credentials'] = str(HTTP_ACCESS_CREDENTIALS).lower()
        response['Access-Control-Allow-Origin']= HTTP_ACCESS_ALLOW_ORIGIN
        response['Access-Control-Allow-Headers'] = request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS', '')

        if LOG_REQUESTS_RESPONSES:
            logger.debug('Outgoing HTTP access response to: %s' %(origin))

        return response
    else:
        # Handle GET request

        if RESTRICT_METHOD_SUMMARY:
            # hide the documentation by raising 404
            raise Http404

        # show documentation
        methods = dispatcher.list_methods()
        template_data = {
            'methods': methods,
            'url': URL,

            # rpc4django version
            'version': version(),

            # restricts the ability to test the rpc server from the docs
            'restrict_rpctest': RESTRICT_RPCTEST,
        }
        return render_to_response('rpc4django/rpcmethod_summary.html', template_data)

# exclude from the CSRF framework because RPC is intended to be used cross site
from django.views.decorators.csrf import csrf_exempt
serve_rpc_request = csrf_exempt(serve_rpc_request)

# reverse the method for use with system.describe and ajax
try:
    URL = reverse(serve_rpc_request)
except NoReverseMatch:
    URL = ''

# resolve JSON_ENCODER to class if it's a string
if isinstance(JSON_ENCODER, basestring):
    mod_name, cls_name = get_mod_func(JSON_ENCODER)
    json_encoder = getattr(import_module(mod_name), cls_name)
else:
    json_encoder = JSON_ENCODER


if not issubclass(json_encoder, json.JSONEncoder):
    raise Exception("RPC4DJANGO_JSON_ENCODER must be derived from "
                    "rpc4django.jsonrpcdispatcher.JSONEncoder")

# instantiate the rpcdispatcher -- this examines the INSTALLED_APPS
# for any @rpcmethod decorators and adds them to the callable methods
dispatcher = RPCDispatcher(URL, APPS, RESTRICT_INTROSPECTION,
        RESTRICT_OOTB_AUTH, json_encoder)

