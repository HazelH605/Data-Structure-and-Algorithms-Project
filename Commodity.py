class Commodity:
    __slots__ = '_name', '_price', '_pop'

    def __init__(self, name, price, popularity):
        self._name = name
        self._price = price
        self._pop = popularity

    def __repr__(self):
        return self._name

    def get_price(self):
        return self._price

    def get_name(self):
        return self._name

    def get_popularity(self):
        return self._pop

    def modify(self, name=None, price=None, popularity=None):
        if name:
            self._name = name
        if price:
            self._price = price
        if popularity:
            self._pop = popularity


class CommoditySearcher:
    """用B+树来实现商品数据范围检索"""
    class _Node:
        """节点类（私有）"""
        __slots__ = 'leaf', 'keys', 'children', 'next', '_m', 'parent'

        def __init__(self, order, leaf=False):
            self.leaf = leaf
            self.keys = []
            self.children = []
            self.next = None
            self._m = order
            self.parent = None

        # 判断节点是否已满
        def has_maximum(self):
            return len(self.keys) == self._m - 1

    def __init__(self, m):
        self._root = self._Node(m, leaf=True)
        self._order = m
        self._min_keys = (self._order + 1) // 2 - 1   # 除了根节点以外的节点的键的数量的最小值

    def _find_child(self, node, price):
        # 如果键的值相同，返回左孩子索引，或者是使得新键插入在值相同的键的左侧的索引
        i = 0
        if node.keys:
            # 用键(price, name)中的price作为主键
            for k, _ in node.keys:
                if price > k:
                    i += 1
                else:
                    break
        return i

    def insert(self, name, price, popularity):
        """插入商品"""
        value = Commodity(name, price, popularity)
        # 用两个元素的元组组成键
        key = (price, name)
        root = self._root
        # 如果根节点已满，先分裂根节点
        if root.has_maximum():
            new_root = self._Node(self._order)
            new_root.children.append(self._root)
            self._root.parent = new_root
            self._split_child(new_root, 0)
            self._root = new_root
        self._insert_nonfull(self._root, key, value)
        return value

    def _insert_nonfull(self, node, key, value):
        idx = self._find_child(node, key[0])
        if node.leaf:
            node.keys.insert(idx, key)
            node.children.insert(idx, value)
        else:
            child = node.children[idx]
            # 下钻过程中遇到已满的节点，就提前分裂
            if child.has_maximum():
                self._split_child(node, idx)
                if key[0] > node.keys[idx][0]:
                    idx += 1
            self._insert_nonfull(node.children[idx], key, value)

    def _split_child(self, parent, idx):
        node = parent.children[idx]
        mid = (self._order - 1) // 2
        split_key = node.keys[mid]
        if node.leaf:
            # 分裂叶子节点，分割键保留在左子节点最后一个
            new_node = self._Node(self._order, leaf=True)
            new_node.keys = node.keys[mid + 1:]
            new_node.children = node.children[mid + 1:]
            node.keys = node.keys[:mid + 1]
            new_node.next = node.next
            node.next = new_node
        else:
            # 分裂内部节点，分割键不在左右子节点中保留
            new_node = self._Node(self._order, leaf=False)
            new_node.keys = node.keys[mid + 1:]
            new_node.children = node.children[mid + 1:]
            node.keys = node.keys[:mid]
        new_node.parent = parent
        node.children = node.children[:mid + 1]
        parent.keys.insert(idx, split_key)
        parent.children.insert(idx + 1, new_node)

    def search_range(self, low, high):
        """查找指定价格范围的所有商品"""
        if low > high:
            raise ValueError('Lower bound exceeds upper bound.')
        node = self._root
        while not node.leaf:
            idx = self._find_child(node, low)
            node = node.children[idx]
        # 定位到价格区间下限的商品所在的叶子节点后，沿着叶子节点的链表指针顺序探测
        result = []
        b = False
        while node:
            for k, v in zip(node.keys, node.children):
                if k[0] >= low:
                    if k[0] <= high:
                        result.append(v)
                    else:
                        b = True
                        break
            if b:
                break
            node = node.next
        return result

    def _search(self, commodity):
        """定位到指定商品所在的叶子节点及其在节点内的索引"""
        price = commodity.get_price()
        node = self._root
        while not node.leaf:
            idx = self._find_child(node, price)
            node = node.children[idx]
        b = False
        leaf_index = None
        while node:
            for i in range(len(node.children)):
                if node.children[i] == commodity:
                    leaf_index = i
                    b = True
                    break
            if b:
                break
            node = node.next
        return node, leaf_index

    def _handle_underflow(self, node):
        parent = node.parent
        if parent is None:
            return
        idx = parent.children.index(node)
        left_sib = parent.children[idx - 1] if idx > 0 else None
        right_sib = parent.children[idx + 1] if idx < len(parent.children) - 1 else None
        # Case 1: 向左兄弟借键
        if left_sib and len(left_sib.keys) > self._min_keys:
            self._borrow_from_left(parent, idx, node, left_sib)
            return
        # Case 2: 向右兄弟借键
        if right_sib and len(right_sib.keys) > self._min_keys:
            self._borrow_from_right(parent, idx, node, right_sib)
            return
        # Case 3: 合并到左兄弟
        if left_sib:
            self._merge_nodes(parent, idx - 1, left_sib, node)
            # 递归处理父节点下溢
            if len(parent.keys) < self._min_keys():
                self._handle_underflow(parent)
            return
        # Case 4: 合并到右兄弟
        if right_sib:
            self._merge_nodes(parent, idx, node, right_sib)
            if len(parent.keys) < self._min_keys:
                self._handle_underflow(parent)

    def _borrow_from_left(self, parent, index, node, left_sib):
        if node.leaf:
            # 叶子节点借键需更新父节点分割键
            borrowed_key = left_sib.keys.pop()
            borrowed_value = left_sib.children.pop()
            node.keys.insert(0, borrowed_key)
            node.children.insert(0, borrowed_value)
            parent.keys[index - 1] = left_sib.keys[-1]
        else:
            # 内部节点借键需处理中间键上移
            borrowed_key = left_sib.keys.pop()
            borrowed_child = left_sib.children.pop()
            node.keys.insert(0, parent.keys[index - 1])
            node.children.insert(0, borrowed_child)
            parent.keys[index - 1] = borrowed_key

    def _borrow_from_right(self, parent, index, node, right_sib):
        if node.leaf:
            # 叶子节点借键需更新父节点分割键
            borrowed_key = right_sib.keys.pop(0)
            borrowed_value = right_sib.children.pop(0)
            node.keys.append(borrowed_key)
            node.children.append(borrowed_value)
            parent.keys[index] = borrowed_key
        else:
            # 内部节点借键需处理中间键下移
            borrowed_key = right_sib.keys.pop(0)
            borrowed_child = right_sib.children.pop(0)
            node.keys.append(parent.keys[index])
            node.children.append(borrowed_child)
            parent.keys[index] = borrowed_key

    def _merge_nodes(self, parent, parent_key_idx, left, right):
        if left.leaf:
            # 合并叶子节点：保持链表连接
            left.keys.extend(right.keys)
            left.children.extend(right.children)
            left.next = right.next
        else:
            # 合并内部节点：需带上父节点的分割键
            left.keys.append(parent.keys[parent_key_idx])
            left.keys.extend(right.keys)
            left.children.extend(right.children)
        # 删除父节点中的分割键和指针
        parent.keys.pop(parent_key_idx)
        parent.children.pop(parent_key_idx + 1)

    def delete(self, commodity):
        """删除商品"""
        node, idx = self._search(commodity)
        if idx is None:
            raise ValueError('Commodity does not exist.')
        node.keys.pop(idx)
        node.children.pop(idx)
        if len(node.keys) < self._min_keys:
            self._handle_underflow(node)
        if not self._root.keys and not self._root.leaf:
            self._root = self._root.children[0]

    def modify(self, commodity, name=None, price=None, pop=None):
        """更改商品信息"""
        if not price:
            node, idx = self._search(commodity)
            p, n = node.keys[idx]
            if name:
                node.keys[idx] = (p, name)
            commodity.modify(name, price, pop)
            node.children[idx] = commodity
        else:
            self.delete(commodity)
            commodity.modify(name, price, pop)
            commodity = self.insert(commodity.get_name(), commodity.get_price(), commodity.get_popularity())
        return commodity