from __future__ import annotations

from collections import deque


def find_clusters(
    grid: list[list[str]],
    min_size: int = 5,
    ignore_symbols: set[str] | None = None,
) -> list[tuple[str, set[tuple[int, int]]]]:
    """
    BFS flood-fill to find all clusters of identical adjacent symbols.

    Returns a list of (symbol, frozenset_of_(row, col)) for every cluster
    whose size >= min_size.  Symbols in *ignore_symbols* (e.g. SCATTER)
    are skipped and never form clusters.

    Grid coordinates: (0, 0) = top-left.
    Adjacency: 4-directional (up / down / left / right).
    """
    if ignore_symbols is None:
        ignore_symbols = {"SCATTER", "EMPTY"}

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    visited: set[tuple[int, int]] = set()
    clusters: list[tuple[str, set[tuple[int, int]]]] = []

    for r in range(rows):
        for c in range(cols):
            symbol = grid[r][c]

            if (r, c) in visited or symbol in ignore_symbols:
                continue

            # BFS
            cluster: set[tuple[int, int]] = set()
            queue: deque[tuple[int, int]] = deque()
            queue.append((r, c))
            visited.add((r, c))

            while queue:
                cr, cc = queue.popleft()
                cluster.add((cr, cc))

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in visited
                        and grid[nr][nc] == symbol
                    ):
                        visited.add((nr, nc))
                        queue.append((nr, nc))

            if len(cluster) >= min_size:
                clusters.append((symbol, cluster))

    return clusters


def calculate_cluster_win(
    clusters: list[tuple[str, set[tuple[int, int]]]],
    paytable: dict[str, dict[int, float]],
) -> float:
    """
    Sum the payout for every winning cluster.

    For a cluster of *size* cells, look up the largest paytable key that is
    <= size (e.g. a 9-cell cluster with keys {5,6,7,8,10,12} pays the '8'
    value).  Clusters larger than the maximum key use the maximum key.
    """
    total = 0.0

    for symbol, positions in clusters:
        if symbol not in paytable:
            continue

        sym_table = paytable[symbol]
        size = len(positions)

        # Clamp to max defined key, then find closest key <= effective_size
        max_key = max(sym_table)
        effective_size = min(size, max_key)
        valid_keys = [k for k in sym_table if k <= effective_size]

        if not valid_keys:
            continue

        closest_key = max(valid_keys)
        total += sym_table[closest_key]

    return total
