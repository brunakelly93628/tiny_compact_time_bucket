import unittest

from tiny_compact_time_bucket import TimeBucket, BucketError


class TestConstruction(unittest.TestCase):

    def test_single_bucket(self):
        tb = TimeBucket([(0, 100)])
        self.assertEqual(tb.buckets, [(0, 100)])

    def test_unsorted_buckets_are_sorted(self):
        tb = TimeBucket([(200, 300), (0, 100), (100, 200)])
        self.assertEqual(tb.buckets, [(0, 100), (100, 200), (200, 300)])

    def test_zero_buckets_rejected(self):
        with self.assertRaises(BucketError):
            TimeBucket([])

    def test_non_tuple_rejected(self):
        with self.assertRaises(TypeError):
            TimeBucket([(1, 2), "x"])

    def test_wrong_arity_rejected(self):
        with self.assertRaises(TypeError):
            TimeBucket([(1, 2, 3)])

    def test_non_numeric_bounds_rejected(self):
        with self.assertRaises(TypeError):
            TimeBucket([("a", "b")])

    def test_bool_bounds_rejected(self):
        with self.assertRaises(TypeError):
            TimeBucket([(True, False)])

    def test_end_le_start_rejected(self):
        with self.assertRaises(BucketError):
            TimeBucket([(100, 100)])
        with self.assertRaises(BucketError):
            TimeBucket([(200, 100)])

    def test_overlapping_buckets_rejected(self):
        with self.assertRaises(BucketError):
            TimeBucket([(0, 150), (100, 200)])

    def test_gap_between_buckets_rejected(self):
        with self.assertRaises(BucketError):
            TimeBucket([(0, 100), (150, 200)])


class TestAssign(unittest.TestCase):

    def setUp(self):
        self.tb = TimeBucket([(0, 10), (10, 30), (30, 100)])

    def test_inside_first_bucket(self):
        self.assertEqual(self.tb.assign(0), 0)
        self.assertEqual(self.tb.assign(5), 0)

    def test_boundary_belongs_to_left_bucket(self):
        self.assertEqual(self.tb.assign(10), 1)
        self.assertEqual(self.tb.assign(30), 2)

    def test_inside_middle_bucket(self):
        self.assertEqual(self.tb.assign(25), 1)

    def test_inside_last_bucket(self):
        self.assertEqual(self.tb.assign(99), 2)

    def test_before_range_rejected(self):
        with self.assertRaises(BucketError):
            self.tb.assign(-1)

    def test_at_or_after_last_end_rejected(self):
        with self.assertRaises(BucketError):
            self.tb.assign(100)
        with self.assertRaises(BucketError):
            self.tb.assign(200)

    def test_non_numeric_timestamp_rejected(self):
        with self.assertRaises(TypeError):
            self.tb.assign("nope")

    def test_bool_timestamp_rejected(self):
        with self.assertRaises(TypeError):
            self.tb.assign(True)


class TestGroup(unittest.TestCase):

    def test_groups_preserve_order_within_bucket(self):
        tb = TimeBucket([(0, 10), (10, 20)])
        result = tb.group([5, 15, 1, 12])
        self.assertEqual(result[0], [5, 1])
        self.assertEqual(result[1], [15, 12])

    def test_empty_input(self):
        tb = TimeBucket([(0, 10)])
        self.assertEqual(tb.group([]), {})

    def test_out_of_range_propagates_error(self):
        tb = TimeBucket([(0, 10)])
        with self.assertRaises(BucketError):
            tb.group([5, 50])


class TestFloatBounds(unittest.TestCase):

    def test_float_timestamps_and_bounds(self):
        tb = TimeBucket([(0.0, 1.5), (1.5, 3.0)])
        self.assertEqual(tb.assign(0.0), 0)
        self.assertEqual(tb.assign(1.5), 1)
        self.assertEqual(tb.assign(2.9), 1)


if __name__ == "__main__":
    unittest.main()
