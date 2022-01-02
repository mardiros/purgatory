Introduction
============

Purgatory is naturally handling many circuits, so circuits are created using
a factory that keep the default configuration for the circuits and for state.

Note that all the parameters of the factory are optionals.

The circuitbreaker will track for exceptions that can be raised in a portion
of code, using a decorator or a ``with`` context.

Example of a circuit breaker that is used with the `httpx`_ library:

.. _`httpx`: https://www.python-httpx.org/

::

   import httpx
   from purgatory import CircuitBreakerFactory

   circuitbreaker = CircuitBreakerFactory(
      default_threshold=5,
      default_ttl=30,
      exclude=[
         (httpx.HTTPStatusError, lambda exc: exc.response.is_client_error),
      ]
   )


The parameter ``default_threshold`` define the default value for all the
failure ``threshold`` of created circuits.

The parameter ``default_ttl`` define the default number of seconds to
keep the circuit opened when the threshold has been reached.

The parameter ``exclude`` is a list  of exceptions, that can be excluded by the
circuit breaker while detecting failure.


Now, we can use our circuit breaker to do an http call:

::

   async with await circuitbreaker.get_breaker("www.example.com"):
      async with httpx.AsyncClient() as client:
          r = await client.get('https://www.example.com/')


At this stage, the method ``get_breaker`` will automatically register
an circuit named ``www.example.com``.

.. note::

   If a circuit with this name has already been registered, it will
   be retrieved to restore it states **and its configuration**.


The default configuration can also be override:

::

   async with await circuitbreaker.get_breaker("www.example.net", threshold=7, ttl=42):
      async with httpx.AsyncClient() as client:
          r = await client.get('https://www.example.net/')


.. important::

   If another circuit breaker `www.example.net` is instanciated, with different
   threshold and ttl, then they are not taken into account.

   The first circuit that register the circuit is configuring it.

   Using a redis backend, updating the threshold or the ttl require to flush
   the keys.


Function can also be decorated as part of a circuit, first example, using
a decorator.

::

   @circuitbreaker("www.example.com")
   async def get_page():
      async with httpx.AsyncClient() as client:
          r = await client.get('https://www.example.com/')


.. note::

   Using a decorator may be elegant but have restriction on circuit name.
   Now they are completly static.
