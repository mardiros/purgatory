3.0.1  - Released on 2024-11-02
-------------------------------
* Fix readme file 

3.0.0  - Released on 2024-11-02
-------------------------------
* Remove support of Python 3.8
* Change license to MIT
* Update packaging to use uv/pdm instead of poetry
* Update of the CI
* Update linting, use ruff instead of flake8

2.0.0  - Released on 2024-05-15
-------------------------------
* Remove support of Python 3.7
* Add support Python 3.12

1.0.3  - Released on 2023-07-29
-------------------------------
* Update dependencies

1.0.2  - Released on 2023-05-10
-------------------------------
* Remove aioredis (replaced by redis.asyncio)
* Update dependencies
* pip install purgatory[aioredis] is kept for compat
  but its install the redis package.

1.0.1  - Released on 2022-05-28
-------------------------------
* Update dependencies

1.0.0  - Released on 2022-02-27
-------------------------------
* Rename package to purgatory

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
