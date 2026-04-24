from typing import Optional
from app.data_structures.transaction_node import TransactionNode

class TransactionLinkedList:
    """
    Append-only LinkedList designed to keep an immutable history of all transactions.
    """
    def __init__(self):
        self.head: Optional[TransactionNode] = None
        self.tail: Optional[TransactionNode] = None

    def append(self, transaction: TransactionNode):
        """
        Appends a new transaction at the end of the list. O(1) insertion.
        """
        if not self.head:
            self.head = transaction
            self.tail = transaction
        else:
            self.tail.next = transaction
            self.tail = transaction

    def __iter__(self):
        """
        Helper method to iterate through nodes naturally: 
        (e.g., [node for node in ll])
        """
        current = self.head
        while current:
            yield current
            current = current.next
