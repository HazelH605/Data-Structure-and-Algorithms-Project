class Empty(Exception):
  pass

class Task:
    __slots__ = '_name', '_urgency', '_impact', '_priority'

    def __init__(self, name, urgency, impact):
        self._name = name
        self._urgency = urgency
        self._impact = impact
        self._priority = self._urgency * self._impact

    def __lt__(self, other):
        return self._priority < other._priority

    def __gt__(self, other):
        return self._priority > other._priority

    def __repr__(self):
        return self._name

    def get_name(self):
        return self._name

    def get_urgency(self):
        return self._urgency

    def get_impact(self):
        return self._impact

    def get_priority(self):
        return self._priority

    def modify(self, name=None, urgency=None, impact=None):
        if name:
            self._name = name
        if urgency:
            self._urgency = urgency
        if impact:
            self._impact = impact
        self._priority = self._urgency * self._impact

class Dependency:
    __slots__ = '_origin', '_destination'

    def __init__(self, task1, task2):
        self._origin = task1
        self._destination = task2

    def __repr__(self):
        return f'{self._destination} 依赖于 {self._origin}'

    def endpoints(self):
        return self._origin, self._destination

class TaskDependency:
    """包含营销任务及其依赖关系的有向图的类"""
    def __init__(self):
        self._outgoing = {}
        self._incoming = {}

    def _validate_task(self, v):
        if not isinstance(v, Task):
            raise TypeError('Task expected')
        if v not in self._outgoing.keys():
            raise ValueError('Task does not exist.')

    def task_count(self):
        return len(self._outgoing)

    def get_all_tasks(self):
        return self._outgoing.keys()

    def get_downstream_tasks(self, task):
        """高效查询下游任务"""
        self._validate_task(task)
        return self._outgoing[task].keys()

    def get_upstream_tasks(self, task):
        """高效查询上游任务"""
        self._validate_task(task)
        return self._incoming[task].keys()

    def _has_path(self, start, target, visited=None):
        """返回从start到target是否存在路径"""
        self._validate_task(start)
        self._validate_task(target)
        if visited is None:
            visited = set()
        if start == target:
            return True
        visited.add(start)
        for neighbor in self._outgoing[start].keys():
            if neighbor not in visited and self._has_path(neighbor, target, visited):
                return True
        return False

    def add_task(self, name, urgency, impact):
        task = Task(name, urgency, impact)
        self._outgoing[task] = {}
        self._incoming[task] = {}
        return task

    def add_dependency(self, task1, task2):
        self._validate_task(task1)
        self._validate_task(task2)
        if self._outgoing[task1].get(task2) is not None:
            raise ValueError('Dependency already exists.')
        if self._has_path(task2, task1):
            raise ValueError('Contradictory dependency')
        relation = Dependency(task1, task2)
        self._outgoing[task1][task2] = relation
        self._incoming[task2][task1] = relation
        return relation

    def modify_task(self, task, name=None, urgency=None, impact=None):
        self._validate_task(task)
        task.modify(name, urgency, impact)

    def remove_task(self, task):
        self._validate_task(task)
        for v in self._outgoing[task].keys():
            del self._incoming[v][task]
        for v in self._incoming[task].keys():
            del self._outgoing[v][task]
        del self._outgoing[task]
        del self._incoming[task]

    def remove_dependency(self, task1, task2):
        self._validate_task(task1)
        self._validate_task(task2)
        if self._outgoing[task1].get(task2) is None:
            raise ValueError('Dependency does not exist.')
        del self._outgoing[task1][task2]
        del self._incoming[task2][task1]

    def degree(self, task, outgoing=True):
        self._validate_task(task)
        adj = self._outgoing if outgoing else self._incoming
        return len(adj[task])

class MaxHeap:
    """包含可执行任务的最大堆，用于实现优先调度功能"""
    def __init__(self):
        self._data = []
        self._map = {}

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for item in self._data:
            yield item

    def is_empty(self):
        return len(self) == 0

    def _parent(self, j):
        return (j - 1) // 2

    def _left(self, j):
        return 2 * j + 1

    def _right(self, j):
        return 2 * j + 2

    def _has_left(self, j):
        return self._left(j) < len(self._data)  # index beyond end of list?

    def _has_right(self, j):
        return self._right(j) < len(self._data)  # index beyond end of list?

    def _swap(self, i, j):
        self._data[i], self._data[j] = self._data[j], self._data[i]
        self._map[self._data[j]] = j
        self._map[self._data[i]] = i

    def _up_heap(self, j):
        parent = self._parent(j)
        if j > 0 and self._data[j] > self._data[parent]:
            self._swap(j, parent)
            self._up_heap(parent)

    def _down_heap(self, j):
        if self._has_left(j):
            left = self._left(j)
            big_child = left
            if self._has_right(j):
                right = self._right(j)
                if self._data[right] > self._data[left]:
                    big_child = right
            if self._data[big_child] > self._data[j]:
                self._swap(j, big_child)
                self._down_heap(big_child)

    def get_all_tasks(self):
        return self._data.copy()

    def get_child(self, task):
        j = self._map.get(task)
        if j is None:
            raise ValueError('Task does not exist.')
        if self._has_left(j):
            left = self._data[self._left(j)]
            if self._has_right(j):
                right = self._data[self._right(j)]
                return left, right
            return left,
        return None

    def add_task(self, task):
        self._data.append(task)
        self._map[task] = len(self._data) - 1
        self._up_heap(len(self._data) - 1)

    def modify_task(self, task, name=None, urgency=None, impact=None):
        j = self._map.get(task)
        if j is None:
            raise ValueError('Task does not exist.')
        task.modify(name, urgency, impact)
        # 任务优先级可能发生变化，分别尝试向上冒泡与向下冒泡来恢复顺序
        if j < len(self._data):
            self._up_heap(j)
            self._down_heap(j)

    def get_top(self):
        if self.is_empty():
            raise Empty('Task schedule is empty.')
        item = self._data[0]
        return item

    def remove_top(self):
        if self.is_empty():
            raise Empty('Task schedule is empty.')
        self._swap(0, len(self._data) - 1)
        top = self._data.pop()
        self._map[top] = None
        self._down_heap(0)
        return top

    def remove_task(self, task):
        """移除堆中任意位置的任务"""
        j = self._map.get(task)
        if j is None:
            raise ValueError('Task does not exist.')
        # 将要移除的任务与最后一个任务交换位置，并移除最后一个任务
        self._swap(j, len(self._data) - 1)
        removed = self._data.pop()
        self._map[removed] = None
        # 尝试向上冒泡与向下冒泡来恢复顺序
        if j < len(self._data):
            self._up_heap(j)
            self._down_heap(j)
        return removed


class TaskScheduler:
    """营销任务调度器，包含一个有向图和一个最大堆"""
    def __init__(self):
        self._graph = TaskDependency()
        self._maxheap = MaxHeap()

    # 对营销任务的操作
    def add_new_task(self, name, urgency, impact):
        # 添加新任务时，同时将其加入有向图和最大堆（因为此时它还没有依赖关系）
        task = self._graph.add_task(name, urgency, impact)
        self._maxheap.add_task(task)
        return task

    def modify_task(self, task, name=None, urgency=None, impact=None):
        self._graph.modify_task(task, name, urgency, impact)
        try:
            self._maxheap.modify_task(task, name, urgency, impact)
        except ValueError:
            pass

    def remove_task(self, task):
        # 删除任务时，考虑对下游任务的影响，如果下游任务不依赖任何任务，则添加至最大堆
        ds = self._graph.get_downstream_tasks(task)
        self._graph.remove_task(task)
        self._maxheap.remove_task(task)
        for t in ds:
            if self._graph.degree(t, outgoing=False) == 0:
                self._maxheap.add_task(t)

    # 对依赖关系的操作
    def add_dependency(self, task1, task2):
        dependency = self._graph.add_dependency(task1, task2)
        try:
            self._maxheap.remove_task(task2)
        except ValueError:
            pass
        return dependency

    def remove_dependency(self, task1, task2):
        # 考虑下游任务，如果不再有依赖则添加至最大堆
        self._graph.remove_dependency(task1, task2)
        if self._graph.degree(task2, outgoing=False) == 0:
            self._maxheap.add_task(task2)

    def top_k_tasks(self, k):
        """查看优先级最高的前k个可执行的任务"""
        if len(self._maxheap) <= k:
            result = [task for task in self._maxheap]
        else:
            result = []
            k_heap = MaxHeap()
            k_heap.add_task(self._maxheap.get_top())
            while len(result) < k:
                top = k_heap.remove_top()
                result.append(top)
                if self._maxheap.get_child(top) is not None:
                    for child in self._maxheap.get_child(top):
                        k_heap.add_task(child)
        return result

    def do_top_task(self):
        """完成优先级最高的可执行的任务"""
        top = self._maxheap.remove_top()
        ds = self._graph.get_downstream_tasks(top)
        self._graph.remove_task(top)
        for t in ds:
            if self._graph.degree(t, outgoing=False) == 0:
                self._maxheap.add_task(t)
        return top

    def task_count(self):
        """返回总任务数量"""
        return self._graph.task_count()

    def get_all_tasks(self):
        """返回所有任务"""
        return self._graph.get_all_tasks()

    def available_task_count(self):
        """返回可执行的任务数量"""
        return len(self._maxheap)

    def get_available_tasks(self):
        """返回所有可执行的任务"""
        return self._maxheap.get_all_tasks()