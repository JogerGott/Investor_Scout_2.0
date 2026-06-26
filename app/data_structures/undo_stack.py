from typing import List, Any, Optional

class UndoStack:
    """
    LIFO Stack structure to keep track of transactions executed in the current session
    so they can be undone.
    """
    def __init__(self):
        self._stack: List[Any] = []

    def push(self, item: Any):
        """Push an element onto the stack."""
        self._stack.append(item)

    def pop(self) -> Optional[Any]:
        """Pop and return the top element of the stack. Returns None if empty."""
        if self.is_empty():
            return None
        return self._stack.pop()

    def peek(self) -> Optional[Any]:
        """Return the top element of the stack without removing it. Returns None if empty."""
        if self.is_empty():
            return None
        return self._stack[-1]

    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._stack) == 0

    def size(self) -> int:
        """Return the size of the stack."""
        return len(self._stack)

    def clear(self):
        """Clear the stack."""
        self._stack.clear()
