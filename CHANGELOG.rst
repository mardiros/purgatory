0.7.2  - Released on 2022-01-18
-------------------------------
* Improve typing

0.7.1  - Released on 2022-01-16
-------------------------------
* Improve typing

0.7.0 (2022-01-04)
------------------
* Add typing support. (PEP 561)
* Validate typing with mypy

0.6.1 (2022-01-04)
------------------
* Bugfix. Add missing failure event when the threshod is attempt.

0.6.0 (2022-01-04)
------------------
* Refactor to get an asynchronous and a synchronous api.

.. important ::

  Breaking Change

  Now the main class export ``CircuitBreakerFactory`` is now
  ``AsyncCircuitBreakerFactory`` and there is a ``SyncCircuitBreakerFactory``
  for synchronous consumers.

0.5.1 (2022-01-02)
------------------
* Add documentation

0.5.0 (2022-01-01)
------------------
* Refactor. Rename model and service.
* Improve typing.
* Publicly expose more classes in the main module.

0.4.0 (2021-12-31)
------------------
* Add a way to monitor circuit breakers.

0.3.0 (2021-12-30)
------------------
* Add an exclude parameter to ignore exception.

0.2.1 (2021-12-29)
------------------
* Add support of redis to share circuit breaker state.

0.2.0 (2021-12-29)
------------------
* Start support of redis to share circuit breaker state.

0.1.0 (2021-12-28)
------------------
* Initial Release.
