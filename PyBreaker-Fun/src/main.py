from decimal import DivisionByZero
import logging
import pybreaker

class Listener(pybreaker.CircuitBreakerListener):
    "Listener used by circuit breakers that execute database operations."
    def before_call(self, cb, func, *args, **kwargs):
        "Called before the circuit breaker `cb` calls `func`."
        #logging.warning('before_call ',cb, func, args, kwargs)
        pass
    def state_change(self, cb, old_state, new_state):
        "Called when the circuit breaker `cb` state changes."
        #logging.warning('state_change ',cb, old_state, new_state)
        pass
    def failure(self, cb, exc):
        "Called when a function invocation raises a system error."
        #logging.warning('failure ',cb, exc)
        logging.warning('DBListener.failure ')
        pass
    def success(self, cb):
        "Called when a function invocation succeeds."
        #logging.warning('success ',cb)
        pass

breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=10, listeners=[Listener()])

@breaker
def doWork():
    logging.warning('\n')
    logging.warning('doWork there we go... ')
    logging.warning('pybreaker: failure counter ' + str(breaker.fail_counter))
    logging.warning('pybreaker: state: ' + str(breaker.current_state))
    raise DivisionByZero

def safeDoWork():
    try:
        logging.warning("start up - before doWork - attempt ")
        doWork()
    except:
        logging.warning("something went wrong")

safeDoWork()
safeDoWork()
safeDoWork()
safeDoWork()

# close the Circuit Breaker allowing work to go trught it
# fail counter will goto ZERO.
breaker.close()
logging.warning('pybreaker: state: ' + str(breaker.current_state))
safeDoWork()
