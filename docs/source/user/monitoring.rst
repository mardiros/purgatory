Monitoring Circuit States
=========================

The circuit breaker factory can register and unregister hook function that
received events from the circuit life and state cycle.

Here is an example of a hook that collect the state metrics of circuits.

::

   from prometheus_client import Counter, Gauge
   from purgatory import AsyncCircuitBreakerFactory


   class GaugeStateValue:
      CLOSED = 0
      HALF_OPEN = 1
      OPEN = 2


   class PrometheusHook:
      def __init__(self):
         circuit_breaker_error = Counter(
            "circuit_breaker_error",
            "Count the circuit breaker exception raised",
            labelnames=["circuit"],
         )

         circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "State of the circuit breaker. 0 is closed, 1 is half-opened, 2 is opened.",
            labelnames=["circuit"],
         )

      def __call__(self, circuit_name: str, evt_type: str, payload: Any) -> None:
         if evt_type == "state_changed":
               state = {
                  "closed": GaugeStateValue.CLOSED,
                  "half-opened": GaugeStateValue.HALF_OPEN,
                  "opened": GaugeStateValue.OPEN,
               }[payload.state]
               self.prometheus_metrics.blacksmith_circuit_breaker_state.labels(
                  circuit_name
               ).set(state)
         elif evt_type == "failed":
               self.prometheus_metrics.blacksmith_circuit_breaker_error.labels(
                  circuit_name
               ).inc()


   circuitbreaker = AsyncCircuitBreakerFactory()
   circuitbreaker.add_listener(PrometheusHook())
