import time

BUDGET_MS = 16.67  # 60 fps target


class Profiler:
    def __init__(self, history_size=60):
        self.last_update_ms = 0.0
        self.peak_ms = 0.0
        self.budget_exceeded_count = 0

        # rolling window of the last N frame times
        self._history = []
        self._history_size = history_size

    @property
    def average_ms(self):
        """ average simulation update time over the last history_size frames"""
        if not self._history:
            return 0.0
        return sum(self._history) / len(self._history)

    def measure(self, func, *args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000.0

        self.last_update_ms = elapsed

        # track worst case ever seen
        if elapsed > self.peak_ms:
            self.peak_ms = elapsed

        # rolling history for average
        self._history.append(elapsed)
        if len(self._history) > self._history_size:
            self._history.pop(0)

        # warn immediately if we blow the budget
        if elapsed > BUDGET_MS:
            self.budget_exceeded_count += 1
            print(
                f"[PROFILER] WARNING: budget exceeded! "
                f"{elapsed:.2f} ms > {BUDGET_MS} ms "
                f"(total violations: {self.budget_exceeded_count})"
            )

        return result