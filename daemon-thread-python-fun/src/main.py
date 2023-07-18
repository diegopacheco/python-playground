import json

class MetricsManager:
    counters = {
        'ok': 0,
        'error': 0
    }

    def registerSucess():
        counters["ok"] += 1

    def registerError():
        counters["error"] += 1

    def get_stats():
        result = json.dumps(counters, indent = 4)
        return result

def main():
    mm = MetricsManager()
    mm.registerSucess
    mm.registerSucess
    print("Result is: " + str(mm.get_stats))

if __name__ == "__main__":
    main()