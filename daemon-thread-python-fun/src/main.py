import json

class MetricsManager(object):
    counters = {
        'ok': 0,
        'error': 0
    }

    def registerSucess(self):
        self.counters["ok"] += 1
        return True

    def registerError(self):
        self.counters["error"] += 1
        return True

    def get_stats(self):
        result = json.dumps(self.counters, indent = 4)
        return result

class ObservableMath(object):
    
    def __init__(self,metrics_manager):
        self.metrics_manager = metrics_manager

    def sum(self,a,b):
        result = a + b
        self.metrics_manager.registerSucess()
        return result

def main():
    mm = MetricsManager()
    math = ObservableMath(mm)
    math.sum(1,1)
    math.sum(2,3)
    math.sum(4,4)
    math.sum(10,34)
    math.sum(56,35)
    math.sum(5645,365)
    math.sum(546,335)

    result = mm.get_stats()
    print("Observability is: " + result)

if __name__ == "__main__":
    main()