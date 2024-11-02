Purgatory
=========

.. image:: https://github.com/mardiros/purgatory/actions/workflows/publish-doc.yml/badge.svg
   :target: https://mardiros.github.io/purgatory/
   :alt: Documentation

.. image:: https://github.com/mardiros/purgatory/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/mardiros/purgatory/actions/workflows/tests.yml
   :alt: Continuous Integration Status

.. image:: https://codecov.io/gh/mardiros/purgatory/branch/main/graph/badge.svg?token=LFVOQC2C9E
   :target: https://codecov.io/gh/mardiros/purgatory
   :alt: Code Coverage Report


Purgatory is a Python library for robust failure management, built to prevent
repetitive errors in synchronous and asynchronous systems through an easy-to-use
circuit breaker pattern.

Circuit breakers are essential in Python failure management, as they help maintain
system safety by preventing cascading failures when dependencies or external services
are temporarily unavailable, ensuring that your application remains stable even under
unpredictable conditions.


.. note::

   Circuit breakers detect failures and encapsulates the logic of preventing
   a failure from constantly recurring, during maintenance, temporary
   external system failure or unexpected system difficulties.

   Source: https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern


Features
--------

Purgatory supports the creation of many circuit breakers easily, that
can be used as context manager or decorator.

Circuit breaker can be asynchronous or synchronous.

Purgatory allows you to store circuit states in multiple backends,
like in-memory or Redis, or even customize the storage backend to suit specific needs.
This flexibility is useful for distributed systems, where keeping state
in a shared location like Redis can improve synchronization.

Purgatory supports monitoring via event hooks, allowing developers to track circuit
state changes and receive notifications on important events (like opening, closing,
or half-opening a circuit).
This feature provides better insight into the system’s health and makes it easier
to react to circuit changes in real time.

Purgatory is fully typed and rigorously tested, which can make it easier to debug and
integrate into larger, type-safe codebases.


Usage
-----

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

.. _`full documentation of this library here`: https://mardiros.github.io/purgatory/user/introduction.html


.. important::

   | The documentation has been moved to github pages.
   | The documentation under readthedocs is obsolete.

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


Why another Circuit Breaker implementation ?
--------------------------------------------

Purgatory has been develop to be used in `Blacksmith`_ where
the library aiobreaker was used but I encountered limitation so,
I decide to build my own implementation that feet well with `Blacksmith`_.

.. _`Blacksmith`: https://mardiros.github.io/blacksmith/
