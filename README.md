# pairing-heap

A min-heap priority queue with amortized O(1) insertion, built on the
pairing heap data structure. Standard library only, no dependencies.

```python
from pairing_heap import PairingHeap

h = PairingHeap()
h.push(3, "low")
h.push(1, "high")
h.push(2, "medium")

print(h.peek())   # (1, 'high')
print(h.pop())    # (1, 'high')
print(h.pop())    # (2, 'medium')
print(len(h))     # 1
```

## Why this exists

Binary heaps give you O(log n) insertion and O(log n) pop. A pairing
heap trades a larger constant on pop for amortized O(1) insertion, which
matters when your workload is insert-heavy — say, a scheduler that
enqueues far more tasks than it dequeues in a given window. The
implementation is also simpler than a Fibonacci heap, with no parent
pointers or cascading-cut bookkeeping.

The trade-off: pop is amortized O(log n) but has a higher constant
factor than a binary heap due to the multi-pass pairing step. If your
workload is pop-heavy or you need worst-case bounds, use something else.

## Exported API

- `PairingHeap` — the queue class.
  - `push(key, value)` — insert an entry. Amortized O(1).
  - `pop() -> (key, value)` — remove and return the minimum entry. Raises `IndexError` if empty.
  - `peek() -> (key, value)` — return the minimum without removing it. Raises `IndexError` if empty.
  - `replace(key, value) -> (key, value)` — pop the current minimum, then push the new entry. Raises `IndexError` if empty.
  - `len(heap)` — number of entries.
  - `iter(heap)` — iterate entries in ascending key order. Non-destructive.

## The awkward edge

**Equal keys are broken by insertion order.** If you push `(1, "a")`
then `(1, "b")`, pop returns `(1, "a")` first. This is deliberate so
that pop order is deterministic for equal keys. If you need a different
tie-break, encode it in your key (e.g., push a tuple `(priority, sub_order)`).

The heap is a **min-heap**. There is no max-heap mode. For a max-heap,
negate your keys.

There is **no decrease-key** operation. Supporting it would require
parent pointers and cut logic that roughly doubles the complexity of the
node structure. If you need to "update" a priority, insert a new entry
and skip the stale one in your consumer code.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

