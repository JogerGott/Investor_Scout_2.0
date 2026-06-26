from collections import deque
from typing import Optional

class SyncQueue:
    """
    FIFO Queue structure to batch process yfinance ticker updates.
    """
    def __init__(self):
        self._queue = deque()

    def enqueue(self, ticker: str):
        """Enqueue a ticker in the queue, preventing duplicates."""
        ticker = ticker.upper().strip()
        if ticker and ticker not in self._queue:
            self._queue.append(ticker)

    def dequeue(self) -> Optional[str]:
        """Dequeue and return the oldest ticker in the queue."""
        if self.is_empty():
            return None
        return self._queue.popleft()

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._queue) == 0

    def size(self) -> int:
        """Return the size of the queue."""
        return len(self._queue)

    def get_all(self) -> list:
        """Return all items in the queue as a list."""
        return list(self._queue)

    def clear(self):
        """Clear the queue."""
        self._queue.clear()
