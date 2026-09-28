import unittest

from pairing_heap import PairingHeap


class TestConstruction(unittest.TestCase):
    def test_new_heap_is_empty(self):
        h = PairingHeap()
        self.assertEqual(len(h), 0)
        self.assertFalse(h)

    def test_peek_on_empty_raises_index_error(self):
        h = PairingHeap()
        with self.assertRaises(IndexError):
            h.peek()

    def test_pop_on_empty_raises_index_error(self):
        h = PairingHeap()
        with self.assertRaises(IndexError):
            h.pop()

    def test_replace_on_empty_raises_index_error(self):
        h = PairingHeap()
        with self.assertRaises(IndexError):
            h.replace(1, "a")
        # Heap must still be empty after the failed replace.
        self.assertEqual(len(h), 0)


class TestPushPop(unittest.TestCase):
    def test_single_push_pop_roundtrip(self):
        h = PairingHeap()
        h.push(5, "five")
        self.assertEqual(len(h), 1)
        self.assertTrue(h)
        self.assertEqual(h.peek(), (5, "five"))
        self.assertEqual(h.pop(), (5, "five"))
        self.assertEqual(len(h), 0)

    def test_pop_returns_minimum_key(self):
        h = PairingHeap()
        for k in [3, 1, 4, 1, 5, 9, 2, 6]:
            h.push(k, str(k))
        results = [h.pop()[0] for _ in range(len(h))]
        self.assertEqual(results, sorted([3, 1, 4, 1, 5, 9, 2, 6]))

    def test_values_preserved_with_keys(self):
        h = PairingHeap()
        h.push(2, "two")
        h.push(1, "one")
        h.push(3, "three")
        self.assertEqual(h.pop(), (1, "one"))
        self.assertEqual(h.pop(), (2, "two"))
        self.assertEqual(h.pop(), (3, "three"))

    def test_peek_does_not_remove(self):
        h = PairingHeap()
        h.push(1, "a")
        h.push(0, "b")
        self.assertEqual(h.peek(), (0, "b"))
        self.assertEqual(len(h), 2)
        self.assertEqual(h.peek(), (0, "b"))


class TestTieBreaking(unittest.TestCase):
    def test_equal_keys_pop_in_insertion_order(self):
        h = PairingHeap()
        h.push(1, "first")
        h.push(1, "second")
        h.push(1, "third")
        self.assertEqual(h.pop(), (1, "first"))
        self.assertEqual(h.pop(), (1, "second"))
        self.assertEqual(h.pop(), (1, "third"))

    def test_tie_breaking_interleaved_with_distinct_keys(self):
        h = PairingHeap()
        h.push(2, "a")
        h.push(1, "b")
        h.push(1, "c")
        h.push(2, "d")
        h.push(1, "e")
        order = [h.pop() for _ in range(5)]
        self.assertEqual(
            order,
            [(1, "b"), (1, "c"), (1, "e"), (2, "a"), (2, "d")],
        )


class TestReplace(unittest.TestCase):
    def test_replace_returns_old_min_and_inserts_new(self):
        h = PairingHeap()
        h.push(1, "old")
        h.push(5, "other")
        old = h.replace(3, "new")
        self.assertEqual(old, (1, "old"))
        # Size unchanged: one removed, one added.
        self.assertEqual(len(h), 2)
        self.assertEqual(h.pop(), (3, "new"))
        self.assertEqual(h.pop(), (5, "other"))

    def test_replace_with_smaller_key_becomes_new_min(self):
        h = PairingHeap()
        h.push(10, "ten")
        h.push(20, "twenty")
        h.replace(5, "five")
        self.assertEqual(h.peek(), (5, "five"))


class TestIteration(unittest.TestCase):
    def test_iter_yields_sorted_order(self):
        h = PairingHeap()
        for k in [7, 2, 5, 1, 9, 3]:
            h.push(k, k * 10)
        items = list(h)
        self.assertEqual(items, [(1, 10), (2, 20), (3, 30), (5, 50), (7, 70), (9, 90)])

    def test_iter_is_non_destructive(self):
        h = PairingHeap()
        for k in [3, 1, 2]:
            h.push(k, str(k))
        first = list(h)
        second = list(h)
        self.assertEqual(first, second)
        self.assertEqual(len(h), 3)

    def test_iter_empty_heap(self):
        h = PairingHeap()
        self.assertEqual(list(h), [])


class TestStress(unittest.TestCase):
    def test_large_random_sequence_matches_sorted(self):
        import random

        rng = random.Random(4242)
        data = [(rng.randint(0, 1000), i) for i in range(500)]
        h = PairingHeap()
        for k, v in data:
            h.push(k, v)
        popped = [h.pop() for _ in range(len(data))]
        # Python's sort is stable, so equal keys keep insertion order,
        # matching our tie-break rule.
        expected = sorted(data, key=lambda kv: kv[0])
        self.assertEqual(popped, expected)

    def test_interleaved_push_pop_maintains_invariant(self):
        h = PairingHeap()
        h.push(5, "e")
        h.push(3, "c")
        self.assertEqual(h.pop(), (3, "c"))
        h.push(1, "a")
        h.push(4, "d")
        self.assertEqual(h.pop(), (1, "a"))
        h.push(2, "b")
        self.assertEqual(h.pop(), (2, "b"))
        self.assertEqual(h.pop(), (4, "d"))
        self.assertEqual(h.pop(), (5, "e"))
        self.assertEqual(len(h), 0)

    def test_negative_and_zero_keys(self):
        h = PairingHeap()
        for k in [0, -5, 3, -1, -10, 7]:
            h.push(k, k)
        result = [h.pop()[0] for _ in range(6)]
        self.assertEqual(result, [-10, -5, -1, 0, 3, 7])

    def test_string_keys_ordered_lexicographically(self):
        h = PairingHeap()
        for s in ["cherry", "apple", "banana", "date"]:
            h.push(s, s)
        result = [h.pop()[0] for _ in range(4)]
        self.assertEqual(result, ["apple", "banana", "cherry", "date"])


if __name__ == "__main__":
    unittest.main()
