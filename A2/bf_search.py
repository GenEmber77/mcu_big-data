"""
Created By: Sagar Kumar
Description: This script implements three methods for nearest neighbour BF search:

  1. Sequential Scan
  2. Best-First Search (BF) on an R-tree
  3. BF with Divide-and-Conquer (sort by y, 4 equal-sized parts, one R-tree each)

Run:
  python bf_search.py <dataset.txt> <query_points_BF.txt> [B]

Example:
  python bf_search.py datasets/data.txt datasets/query_points_BF.txt 4

rtree_gsd.py must be in the same folder.
"""

import sys
import math
import time
import heapq

from rtree_gsd import RTree_GSD, DataPoint, read_points

# =========== Sequential Scan ===========
def sequential_scan(points, qx, qy):
    best_point = None
    best_dist = math.inf
    for p in points:
        d = math.sqrt((p.x - qx) ** 2 + (p.y - qy) ** 2)
        if d < best_dist:
            best_point = p
            best_dist = d
    return best_point, best_dist

# =========== Best-First Search ===========
def bf_search(tree, qx, qy, show_steps=False):
    """Best-First search with one priority queue (heap).

    The heap holds both nodes and points:
      node  -> key = MINDIST from the query to the node's rectangle
      point -> key = real distance from the query to the point
    We always take out the entry with the smallest key.
    The first POINT taken out is the nearest neighbour.
    """
    if tree.size == 0:
        return None, math.inf

    heap = []
    counter = 0      
    heapq.heappush(heap, (0, counter, tree.root))

    while heap:
        key, _, entry = heapq.heappop(heap)

        # a point came out first, so nothing left can be closer
        if isinstance(entry, DataPoint):
            if show_steps:
                print("  pop p%s (%.4f) -> nearest neighbour" % (entry.id, key))
            return entry, key

        if show_steps:
            if entry is tree.root:
                print("  pop U%d (root, key %.4f): expand" % (entry.node_id, key))
            else:
                print("  pop r%d (MINDIST %.4f): expand U%d" % (entry.node_id, key, entry.node_id))

        if entry.is_leaf:
            for p in entry.entries:
                d = math.sqrt((p.x - qx) ** 2 + (p.y - qy) ** 2)
                counter += 1
                heapq.heappush(heap, (d, counter, p))
                if show_steps:
                    print("    push p%s (%.4f)" % (p.id, d))
        else:
            for child in entry.entries:
                d = child.mbr.min_dist(qx, qy)
                counter += 1
                heapq.heappush(heap, (d, counter, child))
                if show_steps:
                    print("    push r%d (%.4f)" % (child.node_id, d))

    return None, math.inf

# =========== BF with Divide-and-Conquer ===========
def bf_divide_and_conquer(trees, qx, qy):
    """Run BF on each subspace's R-tree and return the best result."""
    best_point, best_dist = None, math.inf
    for tree in trees:
        p, d = bf_search(tree, qx, qy)
        if d < best_dist:
            best_point, best_dist = p, d
    return best_point, best_dist

def split_by_y(points, parts=4):
    """Sort by y and cut into equal-sized parts (sizes differ by at most 1)."""
    ordered = sorted(points, key=lambda p: p.y)
    n = len(ordered)
    result = []
    for i in range(parts):
        start = n * i // parts
        end = n * (i + 1) // parts
        result.append(ordered[start:end])
    return result

# =========== main ===========

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return

    # input reading
    data_file = sys.argv[1]
    query_file = sys.argv[2]
    B = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    points = read_points(data_file)
    queries = read_points(query_file)

    # rtree construction
    tree = RTree_GSD.build(points, max_entries=B, show_steps=False)
    parts = split_by_y(points, 4)
    part_trees = [RTree_GSD.build(part, max_entries=B) for part in parts]

    # search methods defined as a list of tuples: (name, output file, search function)
    methods = [
        ("Sequential Scan", "bf_search_sequential_output.txt", lambda qx, qy: sequential_scan(points, qx, qy)),
        ("BF", "bf_search_output.txt", lambda qx, qy: bf_search(tree, qx, qy)),
        ("BF with Divide-and-Conquer", "bf_search_dc_output.txt", lambda qx, qy: bf_divide_and_conquer(part_trees, qx, qy)),
    ]

    # run each search method
    for name, out_file, search in methods:
        summary = []
        summary.append("")
        summary.append("=== Summary ===")
        summary.append("Dataset: %s (%d points), %d queries, B = %d" % (data_file, len(points), len(queries), B))

        # timed: only the searches
        start = time.time()
        results = [search(q.x, q.y) for q in queries]
        total_time = time.time() - start

        section = []
        for q, (p, d) in zip(queries, results):
            section.append("Query %s: id=%s, x=%s, y=%s, distance=%.6f" % (q.id, p.id, p.x, p.y, d))

        # save the summary and results to a file
        summary.append("Search method: %s" % name)
        summary.append("Total running time: %.6f seconds" % total_time)

        # each method is saved to its own file (results, then the summary)
        text = "\n".join(section + summary)
        print(text)
        with open(out_file, "w") as f:
            f.write(text + "\n")
        print("Saved to %s\n" % out_file)


if __name__ == "__main__":
    main()
