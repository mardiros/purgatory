Purgatory
=========

.. image:: https://readthedocs.org/projects/purgatory/badge/?version=latest
   :target: https://purgatory.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/mardiros/purgatory/actions/workflows/main.yml/badge.svg
   :target: https://github.com/mardiros/purgatory/actions/workflows/main.yml
   :alt: Continuous Integration Status

.. image:: https://codecov.io/gh/mardiros/purgatory/branch/main/graph/badge.svg?token=LFVOQC2C9E
   :target: https://codecov.io/gh/mardiros/purgatory
   :alt: Code Coverage Report
    

Purgatory is an implementation of the circuit breaker pattern.

.. note::

   It is used to detect failures and encapsulates the logic of preventing
   a failure from constantly recurring, during maintenance, temporary
   external system failure or unexpected system difficulties. 

   Source: https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern


Why another Circuit Breaker implementation ?
--------------------------------------------

The Purgatory library has been develop to be used in `blacksmith`_ where
the library aiobreaker was used but I encountered limitation so, I decide
to build my own implementation that feet well with `blacksmith`_.


.. _`blacksmith`: https://python-blacksmith.readthedocs.io/en/latest/


Features
--------

Purgatory supports the creation of many circuit breakers easily, that 
can be used as context manager or decorator.
Circuit breaker can be asynchronous or synchronous.

Example with a context manager for an async API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   from purgatory import AsyncCircuitBreakerFactory

   circuitbreaker = AsyncCircuitBreakerFactory()
   async with await circuitbreaker.get_breaker("my_circuit"):
      ...


Example with a decorator
~~~~~~~~~~~~~~~~~~~~~~~~

::

   from purgatory import AsyncCircuitBreakerFactory

   circuitbreaker = AsyncCircuitBreakerFactory()

   @circuitbreaker("another circuit")
   async def function_that_may_fail():
      ...



Example with a context manager for an synchronous API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   from purgatory import SyncCircuitBreakerFactory

   circuitbreaker = SyncCircuitBreakerFactory()
   with circuitbreaker.get_breaker("my_circuit"):
      ...


Circuit breakers states and monitoring
--------------------------------------

The state of every circuits can be stored in memory, shared in redis, or
be completly customized.

It also support monitoring, using event hook.

Purgatory is fully typed and fully tested.


Read More
---------

You can read the `full documentation of this library here`_.

.. _`full documentation of this library here`: https://purgatory.readthedocs.io/en/latest/user/introduction.html


Alternatives
------------

Here is a list of alternatives, which may or may not support coroutines.

 * aiobreaker - https://pypi.org/project/aiobreaker/
 * circuitbreaker - https://pypi.org/project/circuitbreaker/
 * pycircuitbreaker - https://pypi.org/project/pycircuitbreaker/
 * pybreaker - https://pypi.org/project/pybreaker/
 * lasier - https://pypi.org/project/lasier/
 * breakers - https://pypi.org/project/breakers/
 * pybreaker - https://pypi.org/project/pybreaker/
 * python-circuit - https://pypi.org/project/python-circuit/
