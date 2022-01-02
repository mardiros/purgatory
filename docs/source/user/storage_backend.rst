Configuring the storage backend
===============================

Purgatory can share the state of its circuits between many instances using
a redis server.

With this strategy, when a service has been restarted, it starts with
the circuit breaker state.

To choose a storage backend, the unit of work has to be configured.

::

   import httpx
   from purgatory import RedisUnitOfWork
   
   circuit_breaker = CircuitBreakerFactory(
      default_threshold=threshold,
      default_ttl=ttl,
      exclude=[
         (httpx.HTTPStatusError, lambda exc: exc.response.is_client_error),
      ]
      uow=RedisUnitOfWork("redis://localhost/0"),
   )

   await circuit_breaker.initialize()


.. important::

   When using the RedisUnitOfWork, the coroutint ``initialize`` must
   be called to initialize the redis connection.
