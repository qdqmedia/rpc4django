RPC4Django
==========

WARNING
-------

This docs can be outdated since I haven't done yet any revision after latest changes.

   
Prerequisites
-------------

- Python_ 2.4 - 2.7
- Django_ 1.0+ 
- Docutils_ (optional)

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _Docutils: http://docutils.sourceforge.net

Installation
------------

::

    pip install rpc4django

Configuration
-------------

1. First, you need to add new url pattern to your root ``urls.py`` file. 
   You can replace ``r'^RPC2$'`` with anything you like. 
  
    ::
    
        # urls.py 
         
        urlpatterns = patterns('', 
            # rpc4django will need to be in your Python path  
            (r'^RPC2$', 'rpc4django.views.serve_rpc_request'), 
        )
    
2. Second, add RPC4Django to the list of installed applications in your 
   ``settings.py``. 

    ::
    
        # settings.py 
        
        INSTALLED_APPS = ( 
            'rpc4django', 
        )
    
3. Lastly, you need to let RPC4Django know which methods to make available. 
   RPC4Django recursively imports all the apps in ``INSTALLED_APPS`` 
   and makes any methods importable via ``__init__.py`` with the 
   `@rpcmethod` decorator available as RPC methods. You can always write 
   your RPC methods in another module and simply import it in ``__init__.py``. 
  
    ::
    
        # testapp/__init__.py 
        from rpc4django import rpcmethod 
        
        # The doc string supports reST if docutils is installed
        @rpcmethod(name='mynamespace.add', signature=['int', 'int', 'int']) 
        def add(a, b):
            '''Adds two numbers together
            >>> add(1, 2)  
            3  
            '''
        
            return a+b
            
4. For additional information, `read the docs`_

.. _read the docs: http://packages.python.org/rpc4django/

