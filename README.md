# tiny_compact_time_bucket

Groups timestamps into variable-length buckets for data aggregation. You supply the bucket boundaries; the library assigns each timestamp to the correct bucket index and validates the boundaries at construction time.

## Usage

```python
from tiny_compact_time_bucket import TimeBucket, BucketError

buckets = TimeBucket([
    (0, 60),          # last minute
    (60, 3600),       # last hour minus the last minute
    (3600, 86400),    # last day minus the last hour
])

try:
    idx = buckets.assign(120)
except BucketError:
    idx = None

groups = buckets.group([5, 65, 4000, 5000])
# {0: [5], 1: [65], 2: [4000, 5000]}
```

## Why this exists

Rolling-window aggregation often needs buckets of unequal length: a fine-grained recent bucket and coarser historical buckets. Doing this with a fixed `floor(ts / width)` does not work because the width varies. This library makes the bucket layout an explicit, validated input rather than an implicit formula, so the aggregation key is unambiguous and the hot path (assigning a timestamp) is a binary search with no allocations.

The trade-off: you must compute and pass the bucket boundaries yourself. The library will not invent them for you. If you want auto-growing buckets tied to wall-clock time, this is not the right tool.

## Edge cases worth knowing

- Buckets are left-closed, right-open: a timestamp equal to a boundary belongs to the bucket starting at that boundary. The last bucket's end is exclusive, so a timestamp equal to the last end is out of range.
- Buckets must be contiguous with no gaps and no overlaps. `[(0, 10), (10, 20)]` is valid; `[(0, 10), (15, 20)]` raises `BucketError`.
- `bool` is rejected for both bounds and timestamps, even though `bool` is a subclass of `int` in Python, to prevent `True`/`False` silently becoming `1`/`0`.
