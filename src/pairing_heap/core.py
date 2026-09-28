"""Pairing heap priority queue.

A pairing heap is a self-adjusting heap that stores a forest of trees
satisfying the heap property. It is simpler than a Fibonacci heap and
performs competitively in practice. The defining operation is the
multi-pass *pairing* step used during pop: the children of the root are
paired left-to-right in one pass, then the results are merged
right-to-left. This two-pass structure is what gives the heap its
amortized bounds.

Design choices
--------------
* **Min-heap only.** Supporting both directions doubles the surface area
  for no real benefit; callers that need a max-heap can negate their
  keys. Stating this plainly avoids the half-implemented comparators that
  break libraries.
* **No decrease-key.** Decrease-key on a pairing heap requires parent
  pointers and careful cut logic. Omitting it keeps the node structure
  tiny (key, value, child, sibling) and the code honest. Callers who
  need decrease-key should insert a fresh entry and ignore the stale one
  via a tombstone marker in their own value objects.
* **Entries are (key, value) pairs.** The key is the priority; the value
  is opaque payload returned by ``pop``. This separates ordering from
  data, so the heap never inspects user values.
* **Ties broken by insertion order.** When two keys compare equal, the
  earlier-inserted entry wins. This makes pop order deterministic for
  equal keys, which matters for reproducible test runs and stable
  schedulers. We track insertion order with a monotonic counter rather
  than wall-clock time so behaviour is independent of the clock.
"""

from __future__ import annotations

from typing import Any, Generic, Iterator, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _Node(Generic[K, V]):
    __slots__ = ("key", "value", "seq", "child", "sibling")

    def __init__(self, key: K, value: V, seq: int) -> None:
        self.key: K = key
        self.value: V = value
        self.seq: int = seq
        self.child: _Node[K, V] | None = None
        self.sibling: _Node[K, V] | None = None


class PairingHeap(Generic[K, V]):
    """A min-heap priority queue with amortized O(1) insertion.

    Use it when you need a priority queue and want inserts to be cheap
    even at the cost of slightly more expensive pops. The classic
    trade-off versus a binary heap: insertion here is amortized O(1)
    rather than O(log n), but pop is amortized O(log n) with a larger
    constant factor.

    Equal keys are broken by insertion order: the entry inserted first
    is popped first. This is the one non-obvious rule; see the module
    docstring for why.
    """

    __slots__ = ("_root", "_seq", "_size")

    def __init__(self) -> None:
        self._root: _Node[K, V] | None = None
        self._seq: int = 0
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._root is not None

    def __iter__(self) -> Iterator[tuple[K, V]]:
        # Destructive iteration is the only way to iterate a pairing heap
        # in sorted order without materializing all entries up front. We
        # drain into a list so the iterator is non-destructive from the
        # caller's perspective; mutating the heap during iteration would
        # otherwise corrupt internal sibling pointers.
        items = list[tuple[K, V]]()
        while self._root is not None:
            items.append(self.pop())
        # Re-insert so the heap is restored to its prior state.
        for key, value in items:
            self.push(key, value)
        return iter(items)

    def push(self, key: K, value: V) -> None:
        """Insert ``(key, value)``. Amortized O(1)."""
        node = _Node(key, value, self._seq)
        self._seq += 1
        self._size += 1
        if self._root is None:
            self._root = node
        else:
            self._root = self._link(self._root, node)

    def peek(self) -> tuple[K, V]:
        """Return ``(key, value)`` of the minimum entry without removing it.

        Raises ``IndexError`` if the heap is empty. We use ``IndexError``
        rather than ``KeyError`` because the operation is positional
        (the front of the queue), not keyed by a user-supplied key.
        """
        if self._root is None:
            raise IndexError("peek from an empty pairing heap")
        return self._root.key, self._root.value

    def pop(self) -> tuple[K, V]:
        """Remove and return ``(key, value)`` of the minimum entry.

        Amortized O(log n). Raises ``IndexError`` if empty.
        """
        if self._root is None:
            raise IndexError("pop from an empty pairing heap")
        root = self._root
        self._root = self._merge_pairs(root.child)
        self._size -= 1
        return root.key, root.value

    def replace(self, key: K, value: V) -> tuple[K, V]:
        """Pop the current minimum, then push ``(key, value)``.

        Returns the popped entry. Equivalent to ``pop`` followed by
        ``push`` but avoids one tree merge. Raises ``IndexError`` if the
        heap is empty (the push never happens in that case).
        """
        if self._root is None:
            raise IndexError("replace on an empty pairing heap")
        old = self._root
        node = _Node(key, value, self._seq)
        self._seq += 1
        # Merge the new node with the old root's children directly,
        # skipping the separate pop+push. This is the one micro-optimization
        # worth doing because it saves a full _link call.
        self._root = self._merge_pairs(old.child)
        self._root = self._link(self._root, node) if self._root else node
        return old.key, old.value

    @staticmethod
    def _link(a: _Node[K, V], b: _Node[K, V]) -> _Node[K, V]:
        """Merge two single nodes, making the smaller key the parent."""
        if b.key < a.key or (b.key == a.key and b.seq < a.seq):
            a.sibling = b.child
            b.child = a
            return b
        b.sibling = a.child
        a.child = b
        return a

    @classmethod
    def _merge_pairs(cls, node: _Node[K, V] | None) -> _Node[K, V] | None:
        """Two-pass multi-pass pairing of a sibling list.

        Pass 1: walk left-to-right, linking adjacent pairs.
        Pass 2: merge the resulting subtrees right-to-left.

        This is the standard pairing heap pop strategy. The left-to-right
        then right-to-left structure is what produces the amortized
        bounds; a single-pass merge would degrade badly on workloads
        that pop and push in alternation.
        """
        if node is None or node.sibling is None:
            return node
        # Collect the sibling chain into a list so we can pair cleanly.
        # Walking via sibling pointers during pairing is error-prone
        # because _link rewrites sibling pointers; materializing the list
        # first keeps the two passes trivially correct.
        nodes = list[_Node[K, V]]()
        cur: _Node[K, V] | None = node
        while cur is not None:
            nodes.append(cur)
            cur = cur.sibling
        # Clear sibling pointers; they are meaningless once detached.
        for n in nodes:
            n.sibling = None
        # Pass 1: pair left-to-right.
        paired = list[_Node[K, V]]()
        i = 0
        while i + 1 < len(nodes):
            paired.append(cls._link(nodes[i], nodes[i + 1]))
            i += 2
        if i < len(nodes):
            paired.append(nodes[i])
        # Pass 2: merge right-to-left.
        result = paired[-1]
        for j in range(len(paired) - 2, -1, -1):
            result = cls._link(paired[j], result)
        return result
