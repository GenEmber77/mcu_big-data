"""
Created By: Dikshya Senchury
Description: This script implements three methods for nearest neighbour BaB search:

  1. Sequential Scan
  2. Branch-and-Bound (BaB) on an R-tree
  3. BaB with Divide-and-Conquer (4 quadrants, one R-tree each)

Run:
  python bab_search.py <dataset.txt> <query_points.txt> [B]

Example:
  python bab_search.py datasets/data.txt datasets/query_points.txt 4

rtree_gsd.py must be in the same folder.
"""

import sys
import math
import time

from rtree_gsd import RTree_GSD, read_points

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


# =========== Branch-and-Bound ===========
def bab_search(tree, qx, qy, show_steps=False):
    """Depth-first BaB using MINDIST to sort and prune branches."""
    best = {"point": None, "dist": math.inf}

    def check_node(node):
        if node.is_leaf:
            # leaf: check the real distance to every point
            for p in node.entries:
                d = math.sqrt((p.x - qx) ** 2 + (p.y - qy) ** 2)
                if show_steps:
                    print("  leaf U%d: p%s distance %.4f" % (node.node_id, p.id, d))
                if d < best["dist"]:
                    best["point"] = p
                    best["dist"] = d
                    if show_steps:
                        print("    -> new best p%s (%.4f)" % (p.id, d))
            return

        # internal nodes: sorted by MINDIST
        mbrs = []
        for child in node.entries:
            mbrs.append((child.mbr.min_dist(qx, qy), child))
        mbrs.sort(key=lambda item: item[0])

        if show_steps:
            print("  U%d ABL: %s" % (node.node_id, ", ".join(
                "r%d(%.4f)" % (c.node_id, d) for d, c in mbrs)))

        for mindist, child in mbrs:
            if mindist >= best["dist"]:
                # nothing in this child (or any later child) can be closer
                if show_steps:
                    print("  prune r%d: MINDIST %.4f >= best %.4f"
                          % (child.node_id, mindist, best["dist"]))
                break
            if show_steps:
                print("  visit r%d (MINDIST %.4f): open U%d" % (child.node_id, mindist, child.node_id))
            check_node(child)

    if tree.size > 0:
        check_node(tree.root)
    return best["point"], best["dist"]


# =========== BaB with Divide-and-Conquer ===========
def split_into_quadrants(points):
    """Split at the middle of the x range and the middle of the y range."""
    mid_x = (min(p.x for p in points) + max(p.x for p in points)) / 2
    mid_y = (min(p.y for p in points) + max(p.y for p in points)) / 2
    quadrants = [[], [], [], []]
    for p in points:
        if p.x < mid_x and p.y < mid_y:
            quadrants[0].append(p)      # bottom-left
        elif p.x >= mid_x and p.y < mid_y:
            quadrants[1].append(p)      # bottom-right
        elif p.x < mid_x and p.y >= mid_y:
            quadrants[2].append(p)      # top-left
        else:
            quadrants[3].append(p)      # top-right
    return quadrants


def bab_divide_and_conquer(trees, qx, qy):
    """Run BaB on each quadrant's R-tree and return the best result."""
    best_point, best_dist = None, math.inf
    for tree in trees:
        if tree.size == 0:
            continue
        p, d = bab_search(tree, qx, qy)
        if d < best_dist:
            best_point, best_dist = p, d
    return best_point, best_dist


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
    quadrants = split_into_quadrants(points)
    quad_trees = [RTree_GSD.build(q, max_entries=B) for q in quadrants]

    # search methods defined as a list of tuples: (name, output file, search function)
    methods = [
        ("Sequential Scan", "bab_search_sequential_output.txt", lambda qx, qy: sequential_scan(points, qx, qy)),
        ("BaB", "bab_search_output.txt", lambda qx, qy: bab_search(tree, qx, qy)),
        ("BaB with Divide-and-Conquer", "bab_search_dc_output.txt", lambda qx, qy: bab_divide_and_conquer(quad_trees, qx, qy)),
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

        # each method is saved to its own file (with the dataset header)
        text = "\n".join(section + summary)
        print(text)
        with open(out_file, "w") as f:
            f.write(text + "\n")
        print("Saved to %s\n" % out_file)



if __name__ == "__main__":
    main()
