"""
RTree_GSD data structure to hold data points by Genesis, Sagar, Dikshya (GSD)

Contribution:
    Dikshya - DataPoint, MBR, Node, mbr_of_entries
    Genesis - RTree_GSD, init, build, new_node, log, insert_datapoint, pick_subtree, read_points. RTree design and code reviews
    Sagar - do_overflow, split, update_mbrs_up, print_tree

How the tree is built:
  - Insert points one by one into the child node whose bounding box (MBR) expands the least in perimeter (tie-break: smaller area).
  - On overflow (> B entries), split the node by testing all x and y split points, choosing the cut with the minimum total perimeter.
  - If the root splits, create a new root above it, so the tree gets taller.

"""

import math

class DataPoint:
    """One data point from the file: id, x, y."""

    def __init__(self, pid, x, y):
        self.id, self.x, self.y = pid, float(x), float(y)

    def __repr__(self):
        return "p" + str(self.id) + "(" + str(self.x) + ", " + str(self.y) + ")"


class MBR:
    """Minimum bounding rectangle: bottom-left (x1, y1), top-right (x2, y2)."""

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = float(x1), float(y1), float(x2), float(y2)

    def area(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def perimeter(self):
        return 2 * ((self.x2 - self.x1) + (self.y2 - self.y1))

    def perimeter_increase(self, x, y):
        """How much the perimeter grows if we stretch it to cover (x, y)."""
        new_perimeter = 2 * ((max(self.x2, x) - min(self.x1, x)) + (max(self.y2, y) - min(self.y1, y)))
        return new_perimeter - self.perimeter()

    def min_dist_sq(self, x, y):
        """Squared shortest distance from (x, y) to this rectangle (0 if inside)."""
        dx = max(self.x1 - x, 0, x - self.x2)
        dy = max(self.y1 - y, 0, y - self.y2)
        return dx * dx + dy * dy

    def min_dist(self, x, y):
        return math.sqrt(self.min_dist_sq(x, y))

    def __repr__(self):
        return "[(%g, %g), (%g, %g)]" % (self.x1, self.y1, self.x2, self.y2)


def mbr_of_entries(entries):
    """Make the MBR that covers a list of Points or Nodes."""
    if isinstance(entries[0], DataPoint):
        xs1 = xs2 = [p.x for p in entries]
        ys1 = ys2 = [p.y for p in entries]
    else:
        xs1 = [n.mbr.x1 for n in entries]
        ys1 = [n.mbr.y1 for n in entries]
        xs2 = [n.mbr.x2 for n in entries]
        ys2 = [n.mbr.y2 for n in entries]
    return MBR(min(xs1), min(ys1), max(xs2), max(ys2))


class Node:
    """A node in the tree (Uk, k = node_id). A leaf holds Points; an internal
    node holds Nodes, each seen from the parent as its MBR entry rk."""

    def __init__(self, node_id, is_leaf):
        self.node_id = node_id
        self.is_leaf = is_leaf
        self.entries = []
        self.mbr = None
        self.parent = None

    def update_mbr(self):
        self.mbr = mbr_of_entries(self.entries)


class RTree_GSD:
    def __init__(self, max_entries=4, show_steps=False):
        self.B = max_entries                      # max entries per node
        self.m = math.ceil(0.4 * max_entries)     # min entries after a split
        self.show_steps = show_steps              # print steps for the report
        self.next_id = 0
        self.root = self.new_node(True)
        self.size = 0
        self.height = 1

    @classmethod
    def build(cls, points, max_entries=4, show_steps=False):
        tree = cls(max_entries, show_steps)
        for p in points:
            tree.insert_datapoint(p)
        return tree

    def new_node(self, is_leaf):
        node = Node(self.next_id, is_leaf)
        self.next_id += 1
        return node

    def log(self, text):
        if self.show_steps:
            print(text)

    # ---------- insertion ----------

    def insert_datapoint(self, point):
        self.log("\nInsert " + repr(point))

        # 1. go down to a leaf
        node = self.root
        while not node.is_leaf:
            node = self.pick_subtree(node, point)

        # 2. add the point
        node.entries.append(point)
        self.size += 1
        self.log("  added to leaf U%d" % node.node_id)

        # 3. split if overflow, otherwise just fix the rectangles
        to_split = len(node.entries) > self.B
        if to_split:
            self.do_overflow(node)
        else:
            self.update_mbrs_up(node)

    def pick_subtree(self, node, point):
        best = None
        for child in node.entries:
            increase = child.mbr.perimeter_increase(point.x, point.y)
            if best is None or (increase, child.mbr.area()) < best[0]:
                best = ((increase, child.mbr.area()), child)
            self.log("  r%d: perimeter increase %g" % (child.node_id, increase))
        self.log("  -> go to U%d" % best[1].node_id)
        return best[1]

    # ---------- overflow and split ----------

    def do_overflow(self, node):
        while node is not None and len(node.entries) > self.B:
            self.log("  U%d overflows (%d > %d), split it" % (node.node_id, len(node.entries), self.B))
            new_node = self.split(node)

            if node.parent is None:
                # the root split, so make a new root above both halves
                root = self.new_node(False)
                root.entries = [node, new_node]
                node.parent = root
                new_node.parent = root
                root.update_mbr()
                self.root = root
                self.height += 1
                self.log("  new root U%d" % root.node_id)
                return

            # add the new node to the same parent, then check the parent
            parent = node.parent
            parent.entries.append(new_node)
            new_node.parent = parent
            node = parent

        self.update_mbrs_up(node)

    def split(self, node):
        entries = node.entries
        best = None

        for axis in ["x", "y"]:
            if axis == "x":
                ordered = sorted(entries, key=lambda e: e.x if isinstance(e, DataPoint) else e.mbr.x1)
            else:
                ordered = sorted(entries, key=lambda e: e.y if isinstance(e, DataPoint) else e.mbr.y1)

            # try every cut that leaves at least m entries on each side
            for k in range(self.m, len(ordered) - self.m + 1):
                left, right = ordered[:k], ordered[k:]
                cost = mbr_of_entries(left).perimeter() + mbr_of_entries(right).perimeter()
                if best is None or cost < best[0]:
                    best = (cost, axis, left, right)

        cost, axis, left, right = best
        new_node = self.new_node(node.is_leaf)
        node.entries = left
        new_node.entries = right

        # children that moved need to know their new parent
        if not node.is_leaf:
            for child in left:
                child.parent = node
            for child in right:
                child.parent = new_node

        node.update_mbr()
        new_node.update_mbr()
        self.log("  split by %s (perimeter %g): U%d %s | U%d %s" % (
            axis, cost, node.node_id, node.mbr, new_node.node_id, new_node.mbr))
        return new_node

    # ---------- keeping rectangles correct ----------

    def update_mbrs_up(self, node):
        while node is not None:
            node.update_mbr()
            node = node.parent

    # ---------- helpers ----------
    def print_tree(self, node=None, level=0):
        """For debugging: print the tree structure with indentation."""
        if node is None:
            node = self.root
        kind = "leaf" if node.is_leaf else "internal"
        print("  " * level + "U%d (%s) %s" % (node.node_id, kind, node.mbr))
        for e in node.entries:
            if node.is_leaf:
                print("  " * (level + 1) + repr(e))
            else:
                self.print_tree(e, level + 1)


def read_points(path):
    """Read a file with lines 'id x y' into a list of Points."""
    points = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3:
                pid = int(parts[0]) if parts[0].isdigit() else parts[0]
                points.append(DataPoint(pid, parts[1], parts[2]))
    return points
