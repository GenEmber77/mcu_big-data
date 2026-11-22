"""
Created By: Genesis Emberga
Description: This script implements three methods for skyline BBS search
(lower x = total cost and lower y = price per m2 are better):

  1. Sequential Scan
  2. Branch-and-Bound Skyline (BBS) on an R-tree
  3. BBS with Divide-and-Conquer (sort by x, 2 halves, one R-tree each,
     then merge the two local skylines)

Run:
  python bbs_search.py <city.txt> [B]

Example:
  python bbs_search.py datasets/city3.txt 5

rtree_gsd.py must be in the same folder.
"""

import sys
import time
import heapq

from rtree_gsd import RTree_GSD, DataPoint, read_points


# =========== Dominance checks ===========
def dominates(a_x, a_y, b_x, b_y):
    """True if (a_x, a_y) dominates (b_x, b_y):
    no worse in both values and strictly better in at least one."""
    return a_x <= b_x and a_y <= b_y and (a_x < b_x or a_y < b_y)


def is_dominated(x, y, skyline):
    """True if any point already in the skyline dominates (x, y)."""
    for s in skyline:
        if dominates(s.x, s.y, x, y):
            return True
    return False


# =========== Sequential Scan ===========
def sequential_scan(points):
    """Keep every point that no other point dominates."""
    skyline = []
    for p in points:
        dominated = False
        for q in points:
            if dominates(q.x, q.y, p.x, p.y):
                dominated = True
                break
        if not dominated:
            skyline.append(p)
    return skyline


# =========== Branch-and-Bound Skyline ===========
def bbs_skyline(tree, show_steps=False):
    """BBS with one priority queue (heap).

    Key = x + y (distance to the origin (0, 0)):
      node  -> x1 + y1 of its rectangle (bottom-left corner)
      point -> x + y
    A point can only be dominated by a point with a smaller x + y,
    so when a point comes out of the heap, all points that could
    dominate it have already come out.

    A node is skipped when a skyline point dominates its bottom-left
    corner, because then it dominates every point inside the node.
    """
    skyline = []
    if tree.size == 0:
        return skyline

    heap = []
    counter = 0  
    root = tree.root
    heapq.heappush(heap, (root.mbr.x1 + root.mbr.y1, counter, root))

    while heap:
        key, _, entry = heapq.heappop(heap)

        if isinstance(entry, DataPoint):
            if is_dominated(entry.x, entry.y, skyline):
                if show_steps:
                    print("  pop p%s (%g): dominated, discard" % (entry.id, key))
            else:
                skyline.append(entry)
                if show_steps:
                    print("  pop p%s (%g): add to skyline" % (entry.id, key))
            continue

        # entry is a node: skip it if its bottom-left corner is dominated
        if is_dominated(entry.mbr.x1, entry.mbr.y1, skyline):
            if show_steps:
                print("  pop r%d (%g): corner dominated, prune U%d"
                      % (entry.node_id, key, entry.node_id))
            continue

        if show_steps:
            if entry is root:
                print("  pop U%d (root, %g): expand" % (entry.node_id, key))
            else:
                print("  pop r%d (%g): expand U%d" % (entry.node_id, key, entry.node_id))

        for child in entry.entries:
            if entry.is_leaf:
                x, y = child.x, child.y
            else:
                x, y = child.mbr.x1, child.mbr.y1
            if not is_dominated(x, y, skyline):
                counter += 1
                heapq.heappush(heap, (x + y, counter, child))
            elif show_steps:
                print("    not pushed: %s (dominated)"
                      % ("p%s" % child.id if entry.is_leaf else "r%d" % child.node_id))

    return skyline


# =========== BBS with Divide-and-Conquer ===========
def bbs_divide_and_conquer(left_tree, right_tree):
    """Run BBS on each half's R-tree, then merge the two local skylines."""
    left_skyline = bbs_skyline(left_tree)
    right_skyline = bbs_skyline(right_tree)
    return merge_skylines(left_skyline, right_skyline)

def split_by_x(points):
    """Sort by x (ties by y) and cut into two equal halves."""
    ordered = sorted(points, key=lambda p: (p.x, p.y))
    half = len(ordered) // 2
    return ordered[:half], ordered[half:]


def merge_skylines(left_skyline, right_skyline):
    """Combine the two local skylines using 1-d dominance screening.

    Every left point has x <= every right point (we sorted by x),
    so a left point can never be dominated by a right point.
    A right point only needs to be checked against the left point
    with the lowest y: if that y is lower, the right point is dominated.
    """
    if len(left_skyline) == 0:
        return right_skyline

    best_left = min(left_skyline, key=lambda p: (p.y, p.x))
    result = list(left_skyline)
    for r in right_skyline:
        if not dominates(best_left.x, best_left.y, r.x, r.y):
            result.append(r)
    return result

# =========== main ===========

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    # input reading
    data_file = sys.argv[1]
    B = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    points = read_points(data_file)

    # rtree construction
    tree = RTree_GSD.build(points, max_entries=B, show_steps=False)
    left, right = split_by_x(points)
    left_tree = RTree_GSD.build(left, max_entries=B)
    right_tree = RTree_GSD.build(right, max_entries=B)

    # search methods defined as a list of tuples: (name, output file, search function)
    methods = [
        ("Sequential Scan", "bbs_search_sequential_output.txt", lambda: sequential_scan(points)),
        ("BBS", "bbs_search_output.txt", lambda: bbs_skyline(tree)),
        ("BBS with Divide-and-Conquer", "bbs_search_dc_output.txt", lambda: bbs_divide_and_conquer(left_tree, right_tree)),
    ]

    # run each search method
    for name, out_file, search in methods:
        summary = []
        summary.append("")
        summary.append("=== Summary ===")
        summary.append("Dataset: %s (%d points), B = %d" % (data_file, len(points), B))

        # timed: only the skyline search
        start = time.time()
        skyline = search()
        total_time = time.time() - start

        # sort by x ascending, ties by y, as the spec asks
        skyline = sorted(skyline, key=lambda p: (p.x, p.y))

        section = []
        for p in skyline:
            section.append("id=%s, x=%s, y=%s" % (p.id, p.x, p.y))

        # save the summary and results to a file
        summary.append("Number of skyline points: %d" % len(skyline))
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
