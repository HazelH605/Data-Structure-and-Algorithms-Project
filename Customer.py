class Customer:
    __slots__ = '_name'

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name


class Relationship:
    __slots__ = '_origin', '_destination', '_weight'

    def __init__(self, u, v, weight):
        if weight > 1 or weight < 0:
            raise ValueError('Weight must be between 0 and 1.')
        self._origin = u
        self._destination = v
        self._weight = weight

    def __repr__(self):
        return f'from {self._origin} to {self._destination} weight {self._weight}'

    def get_weight(self):
        return self._weight

    def opposite(self, v):
        if not isinstance(v, Customer):
            raise TypeError('Customer expected')
        if v is self._origin:
            return self._destination
        elif v is self._destination:
            return self._origin
        else:
            raise ValueError('Customer is not incident to this relationship.')


class CustomerNetwork:
    """用加权有向图实现客户网络与影响力传播分析，节点为Customer类，边为Relationship类"""
    def __init__(self):
        self._outgoing = {}
        self._incoming = {}

    def _validate_customer(self, v):
        if not isinstance(v, Customer):
            raise TypeError('Customer expected')
        if v not in self._outgoing:
            raise ValueError('Customer does not belong to this company.')

    def customer_count(self):
        return len(self._outgoing)

    def relationship_count(self):
        total = sum(len(self._outgoing[v]) for v in self._outgoing)
        return total

    def get_customers(self):
        return self._outgoing

    def get_relationships(self):
        relations = []
        for secondary_map in self._outgoing.values():
            relations.extend(secondary_map.values())
        return relations

    def get_relationship(self, u, v):
        self._validate_customer(u)
        self._validate_customer(v)
        return self._outgoing[u].get(v)

    def incident_edges(self, v):
        return list(self._outgoing[v].values())

    def add_customer(self, name):
        v = Customer(name)
        self._outgoing[v] = {}
        self._incoming[v] = {}
        return v

    def add_relationship(self, u, v, weight):
        if self.get_relationship(u, v) is not None:
            raise ValueError('Relationship already exists.')
        relationship = Relationship(u, v, weight)
        self._outgoing[u][v] = relationship
        self._incoming[v][u] = relationship
        return relationship

    def degree(self, v, outgoing=True):
        self._validate_customer(v)
        adj = self._outgoing if outgoing else self._incoming
        return len(adj[v])

    def page_rank(self, d=0.85, max_iter=100, tol=1e-9):
        """返回所有客户的page rank值（重要性）的列表"""
        in_weights = {c:sum([w.get_weight() for w in self._incoming[c].values()]) for c in self._incoming}
        n = len(self._incoming)
        pr = dict.fromkeys(self._incoming, 1/n)
        for i in range(max_iter):
            leak = 0
            new_pr = dict.fromkeys(self._incoming.keys(), 0)
            for c in self._incoming:
                if in_weights[c] == 0:
                    leak += d * pr[c] / n
                else:
                    for v, w in self._incoming[c].items():
                        new_pr[v] += d * pr[c] * w.get_weight() / in_weights[c]
            for c in self._incoming:
                new_pr[c] += (1-d)/n + leak
            diff = sum(abs(new_pr[c] - pr[c]) for c in self._incoming)
            if diff < tol:
                break
            pr = new_pr
        return pr

    def _dfs(self, customer, discovered):
        for o in self._outgoing[customer]:
            if o not in discovered:
                discovered.append(o)
                self._dfs(o, discovered)

    def reachable_customers(self):
        """返回每一位客户能影响到的所有其他客户"""
        result = {}
        for customer in self._outgoing:
            discovered = [customer]
            self._dfs(customer, discovered)
            result[customer] = discovered
        return result

    def _dfs_pruned(self, customer, reached, max_depth, min_influence, depth=0, influence=1):
        for o in self._outgoing[customer]:
            current_depth = depth + 1
            current_influence = influence*self._outgoing[customer][o].get_weight()
            if current_depth <= max_depth and current_influence >= min_influence:
                if not o in reached:
                    reached.append(o)
                self._dfs_pruned(o, reached, max_depth, min_influence, current_depth, current_influence)

    def reachable_customers_pruned(self, max_depth, min_influence):
        """当影响路径超过max_depth层，路径影响力小于min_influence时，忽略影响。返回每一位客户能影响到的所有其他客户。"""
        result = {}
        for customer in self._outgoing:
            reached = [customer]
            self._dfs_pruned(customer, reached, max_depth, min_influence)
            result[customer] = reached
        return result

