import time


class Profiler:
    def __init__(self):
        self.last_update_ms = 0.0

    def measure(self, func, *args, **kwargs):
        
        # high precision timer
        start = time.perf_counter()
        
        # run the function to measure
        result = func(*args, **kwargs)
        end = time.perf_counter()
        
        self.last_update_ms = (end - start) * 1000.0
        return result