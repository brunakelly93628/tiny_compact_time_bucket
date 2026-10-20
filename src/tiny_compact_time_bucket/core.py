from __future__ import annotations


class BucketError(ValueError):
    """Raised when bucket boundaries or durations are inconsistent.

    We subclass ValueError so callers that already catch ValueError for bad
    numeric input also catch structural problems, while callers who care about
    bucket integrity specifically can catch BucketError.
    """


class TimeBucket:
    """Group timestamps into variable-length buckets for data aggregation.

    A bucket is defined by a (start, end) interval, half-open: start is
    included, end is excluded. The intended use is rolling aggregation where
    the current bucket may be short (recent activity) and older buckets cover
    progressively longer spans.

    Design decisions (stated plainly so the tests and README agree):

    1. Buckets are supplied by the caller as a list of (start, end) tuples.
       We sort and validate them; we do not invent buckets. This keeps the
       model explicit and avoids hidden "auto-grow" behaviour that would
       be non-deterministic without a clock.

    2. A timestamp exactly on a boundary belongs to the bucket whose start
       equals it (left-closed). The final bucket is also left-closed but
       right-open at its stated end. Timestamps at or beyond the last end, or
        before the first start, are out of range and raise BucketError.

    3. Overlapping buckets are an error. So are non-monotonic starts, zero or
       negative durations, and gaps between adjacent buckets. These checks
       happen at construction so the hot path (assign) is allocation-free.

    4. assign() returns the bucket index (int), not the bucket tuple. The
       caller already has the list; returning the index avoids tuple copies
       and gives a stable key for grouping.
    """

    def __init__(self, buckets):
        if not isinstance(buckets, (list, tuple)):
            raise TypeError("buckets must be a list or tuple of (start, end) pairs")
        if len(buckets) == 0:
            raise BucketError("at least one bucket is required")

        normalized = []
        for b in buckets:
            if not isinstance(b, (list, tuple)) or len(b) != 2:
                raise TypeError("each bucket must be a (start, end) pair")
            start, end = b[0], b[1]
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                raise TypeError("bucket bounds must be int or float")
            if isinstance(start, bool) or isinstance(end, bool):
                # bool is a subclass of int in Python; reject it explicitly so
                # that True/False do not silently become 1/0 bounds.
                raise TypeError("bucket bounds must be int or float, not bool")
            if end <= start:
                raise BucketError(
                    "bucket end must be greater than start; got (%r, %r)" % (start, end)
                )
            normalized.append((start, end))

        normalized.sort(key=lambda pair: pair[0])

        for i in range(1, len(normalized)):
            prev_end = normalized[i - 1][1]
            cur_start = normalized[i][0]
            if cur_start < prev_end:
                raise BucketError("buckets overlap: %r and %r" %
                                  (normalized[i - 1], normalized[i]))
            if cur_start > prev_end:
                raise BucketError("gap between buckets: %r ends at %r, next starts at %r"
                                  % (normalized[i - 1], prev_end, cur_start))

        self._buckets = normalized
        self._starts = [b[0] for b in normalized]
        self._ends = [b[1] for b in normalized]

    @property
    def buckets(self):
        return list(self._buckets)

    def assign(self, timestamp):
        if not isinstance(timestamp, (int, float)):
            raise TypeError("timestamp must be int or float")
        if isinstance(timestamp, bool):
            raise TypeError("timestamp must be int or float, not bool")
        if timestamp < self._starts[0] or timestamp >= self._ends[-1]:
            raise BucketError("timestamp %r is outside bucket range [%r, %r)"
                              % (timestamp, self._starts[0], self._ends[-1]))
        lo, hi = 0, len(self._buckets) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            start, end = self._buckets[mid]
            if timestamp < start:
                hi = mid - 1
            elif timestamp >= end:
                lo = mid + 1
            else:
                return mid
        raise BucketError("timestamp %r could not be assigned" % timestamp)

    def group(self, timestamps):
        groups = {}
        for ts in timestamps:
            idx = self.assign(ts)
            groups.setdefault(idx, []).append(ts)
        return groups
