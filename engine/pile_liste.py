class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Liste_chaine:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
        else:
            self.tail.next = new_node
        self.tail = new_node
        self.size += 1

    def pop(self):
        if not self.head:
            return None
        if self.head == self.tail:
            data = self.head.data
            self.head = self.tail = None
            self.size -= 1
            return data
        current = self.head
        while current.next != self.tail:
            current = current.next
        data = self.tail.data
        current.next = None
        self.tail = current
        self.size -= 1
        return data

    def __len__(self):
        return self.size


class Pile_LIFO:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None

    def is_empty(self):
        return len(self.items) == 0

    def __len__(self):
        return len(self.items)
