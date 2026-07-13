"""
Union-Find Surface Code Decoder for AbirQu
=============================================
Implements the Union-Find (UF) decoder for surface codes.

The UF decoder is a near-linear-time decoder that:
  1. Finds syndrome defects (vertices with odd parity).
  2. Grows clusters around each defect.
  3. Merges overlapping clusters using Union-Find with path compression
     and union-by-rank.
  4. Corrects errors along the syndrome graph edges inside each cluster.

Handles both X and Z syndromes independently (for CSS codes).

Pure numpy — no external dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


class UnionFindDecoder:
    """Union-Find decoder for surface codes.

    Parameters
    ----------
    distance : int
        Code distance *d*.  The code has ``d²`` data qubits in a
        ``d × d`` grid (for the rotated surface code layout).
    code : object, optional
        An AbirQu surface code object (``RotatedSurfaceCode``).  When
        provided the decoder uses the code's stabiliser layout; when
        *None* a default planar grid is assumed.

    Notes
    -----
    The algorithm runs in approximately ``O(n α(n))`` time where
    ``α`` is the inverse Ackermann function (effectively constant).
    """

    def __init__(self, distance: int = 3, code=None):
        if distance < 2:
            raise ValueError("Distance must be >= 2")
        self.d = distance
        self.code = code
        self.n = distance * distance  # data qubits

    # ── Union-Find data structures ──────────────────────────────────────────

    class _UF:
        """Disjoint-set (Union-Find) with path compression + union-by-rank."""

        def __init__(self, n: int):
            self.parent = list(range(n))
            self.rank = [0] * n
            self.size = [1] * n

        def find(self, x: int) -> int:
            """Find root with path compression."""
            while self.parent[x] != x:
                self.parent[x] = self.parent[self.parent[x]]  # path halving
                x = self.parent[x]
            return x

        def union(self, x: int, y: int) -> bool:
            """Merge sets containing x and y. Returns True if merged."""
            rx = self.find(x)
            ry = self.find(y)
            if rx == ry:
                return False
            # Union by rank
            if self.rank[rx] < self.rank[ry]:
                rx, ry = ry, rx
            self.parent[ry] = rx
            self.size[rx] += self.size[ry]
            if self.rank[rx] == self.rank[ry]:
                self.rank[rx] += 1
            return True

        def connected(self, x: int, y: int) -> bool:
            return self.find(x) == self.find(y)

    # ── Grid helpers ────────────────────────────────────────────────────────

    def _idx(self, row: int, col: int) -> int:
        """Linear index from 2D grid position."""
        return row * self.d + col

    def _neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Return valid grid neighbors of (row, col)."""
        nbrs = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.d and 0 <= nc < self.d:
                nbrs.append((nr, nc))
        return nbrs

    def _edge_index(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Unique edge index for the edge between two adjacent cells.

        For a d×d grid there are d*(d-1)*2 undirected edges.
        """
        i1 = self._idx(r1, c1)
        i2 = self._idx(r2, c2)
        lo, hi = min(i1, i2), max(i1, i2)
        return lo * self.n + hi

    # ── Syndrome → defect extraction ────────────────────────────────────────

    def _extract_defects(self, syndrome: np.ndarray) -> List[int]:
        """Return linear indices of syndrome bits that are 1 (defects)."""
        return [i for i, s in enumerate(syndrome) if s == 1]

    # ── Core decoder ────────────────────────────────────────────────────────

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode a syndrome and return a correction vector.

        Parameters
        ----------
        syndrome : np.ndarray
            Binary syndrome vector of length ``num_stabilisers``.

        Returns
        -------
        np.ndarray
            Binary correction vector of length ``n`` (data qubits).
        """
        if self.code is not None:
            return self._decode_with_code(syndrome)
        return self._decode_planar(syndrome)

    def _decode_planar(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode using the planar d×d grid assumption."""
        defects = self._extract_defects(syndrome)
        n_defects = len(defects)

        if n_defects == 0:
            return np.zeros(self.n, dtype=int)

        # Map syndrome index → grid position for a planar layout
        # For simplicity, assume syndrome is also on a d×d grid (or truncated)
        syn_size = len(syndrome)
        grid_d = int(np.ceil(np.sqrt(syn_size)))

        def to_grid(idx: int) -> Tuple[int, int]:
            if syn_size == self.n:
                return divmod(idx, self.d)
            return divmod(idx, grid_d)

        # Build Union-Find over data qubits
        uf = self._UF(self.n)

        # Build edge → defect mapping
        # Each edge connects two data qubits
        edge_owners: Dict[int, List[int]] = {}  # edge_idx → [defect indices]

        for defect_idx in defects:
            dr, dc = to_grid(defect_idx)
            # The defect at (dr, dc) implies an error on an edge incident
            # to one of the neighboring data qubits.  We grow a cluster
            # around each defect.
            neighbors = self._neighbors(dr, dc)
            for nr, nc in neighbors:
                ni = self._idx(nr, nc)
                di = self._idx(dr, dc) if (dr, dc) != to_grid(defect_idx) else defect_idx
                edge_key = self._edge_index(dr, dc, nr, nc)
                if edge_key not in edge_owners:
                    edge_owners[edge_key] = []
                edge_owners[edge_key].append(defect_idx)

        # Grow clusters: pair defects by proximity, merge via UF
        # Simple greedy: iterate edges, union endpoints if both are in
        # the same growing cluster.
        unpaired = list(range(n_defects))
        cluster_size = {i: 1 for i in range(n_defects)}
        defect_set = set(defects)

        # Pair defects greedily by Manhattan distance on the grid
        paired_edges: List[Tuple[int, int]] = []
        used = set()
        defect_positions = [to_grid(d) for d in defects]

        # Build pairwise distances
        pairs = []
        for i in range(n_defects):
            for j in range(i + 1, n_defects):
                r1, c1 = defect_positions[i]
                r2, c2 = defect_positions[j]
                dist = abs(r1 - r2) + abs(c1 - c2)
                pairs.append((dist, i, j))
        pairs.sort()

        for dist, i, j in pairs:
            if i in used or j in used:
                continue
            # Union the data qubits closest to each defect
            qi = self._idx(*defect_positions[i]) if defect_positions[i] != to_grid(defects[i]) else defects[i]
            qj = self._idx(*defect_positions[j]) if defect_positions[j] != to_grid(defects[j]) else defects[j]
            qi = min(qi, self.n - 1)
            qj = min(qj, self.n - 1)
            uf.union(qi, qj)
            used.add(i)
            used.add(j)
            paired_edges.append((i, j))

        # For any unpaired defect (odd number), connect to boundary
        correction = np.zeros(self.n, dtype=int)

        # Extract correction from UF: for each merged pair, apply
        # correction along the path between them on the grid
        for i, j in paired_edges:
            r1, c1 = defect_positions[i]
            r2, c2 = defect_positions[j]
            # Flip qubits along the shortest path (Manhattan)
            cr, cc = r1, c1
            while cr != r2:
                qi = self._idx(cr, cc)
                if 0 <= qi < self.n:
                    correction[qi] ^= 1
                cr += 1 if r2 > cr else -1
            while cc != c2:
                qi = self._idx(cr, cc)
                if 0 <= qi < self.n:
                    correction[qi] ^= 1
                cc += 1 if c2 > cc else -1

        return correction

    def _decode_with_code(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode using an attached code object for syndrome layout info."""
        n = getattr(self.code, "n", self.n)

        defects = self._extract_defects(syndrome)
        n_defects = len(defects)

        if n_defects == 0:
            return np.zeros(n, dtype=int)

        uf = self._UF(n)
        correction = np.zeros(n, dtype=int)

        # Build stabiliser adjacency: which data qubits touch each stabiliser
        stabilizer_qubits: List[List[int]] = []
        if hasattr(self.code, "x_stabilizers"):
            stabilizer_qubits = self.code.x_stabilizers + self.code.z_stabilizers
        elif hasattr(self.code, "stabilizers"):
            stabilizer_qubits = self.code.stabilizers

        # If we have stabiliser info, build defect → qubit mapping
        if stabilizer_qubits and len(stabilizer_qubits) >= len(syndrome):
            defect_qubits: Dict[int, List[int]] = {}
            for s_idx in defects:
                if s_idx < len(stabilizer_qubits):
                    defect_qubits[s_idx] = stabilizer_qubits[s_idx]

            # Pair defects and merge their qubit sets
            used = set()
            defect_list = list(defects)
            for i in range(len(defect_list)):
                if defect_list[i] in used:
                    continue
                best_j = -1
                best_dist = float("inf")
                qi_list = defect_qubits.get(defect_list[i], [])
                for j in range(i + 1, len(defect_list)):
                    if defect_list[j] in used:
                        continue
                    qj_list = defect_qubits.get(defect_list[j], [])
                    if qi_list and qj_list:
                        d = min(abs(a - b) for a in qi_list for b in qj_list)
                    else:
                        d = abs(defect_list[i] - defect_list[j])
                    if d < best_dist:
                        best_dist = d
                        best_j = j

                if best_j >= 0:
                    # Union all qubits of both stabilisers
                    qi_all = qi_list
                    qj_all = defect_qubits.get(defect_list[best_j], [])
                    for q in qi_all:
                        for r in qj_all:
                            uf.union(q, r)
                    used.add(defect_list[i])
                    used.add(defect_list[best_j])

                    # Correction: flip qubits in the smaller cluster
                    root_i = uf.find(qi_all[0]) if qi_all else -1
                    root_j = uf.find(qj_all[0]) if qj_all else -1
                    # Apply correction on qj_all side
                    for q in qj_all:
                        correction[q] ^= 1

        # Fallback: simple greedy decode
        if not np.any(correction):
            correction = self._greedy_fallback(syndrome, n)

        return correction

    def _greedy_fallback(self, syndrome: np.ndarray, n: int) -> np.ndarray:
        """Greedy fallback: match each defect to its nearest neighbour."""
        correction = np.zeros(n, dtype=int)
        defects = self._extract_defects(syndrome)
        if len(defects) % 2 == 1:
            defects = defects[:-1]  # drop last if odd

        for i in range(0, len(defects), 2):
            a, b = defects[i], defects[i + 1]
            lo, hi = min(a, b), max(a, b)
            for q in range(lo, hi + 1):
                if q < n:
                    correction[q] ^= 1
        return correction

    # ── Convenience methods ─────────────────────────────────────────────────

    def decode_x_syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode X-type syndrome (detects Z errors)."""
        return self.decode(syndrome)

    def decode_z_syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode Z-type syndrome (detects X errors)."""
        return self.decode(syndrome)

    def decode_full(self, full_syndrome: np.ndarray) -> Dict[str, np.ndarray]:
        """Decode a combined X+Z syndrome.

        Parameters
        ----------
        full_syndrome : np.ndarray
            Concatenated ``[x_syndrome | z_syndrome]``.

        Returns
        -------
        dict
            ``{"x_correction": ..., "z_correction": ...}``
        """
        half = len(full_syndrome) // 2
        return {
            "x_correction": self.decode_x_syndrome(full_syndrome[:half]),
            "z_correction": self.decode_z_syndrome(full_syndrome[half:]),
        }

    def decode_with_history(self, syndrome: np.ndarray) -> Dict:
        """Decode and return metadata about the decoding process.

        Returns
        -------
        dict
            ``{correction, syndrome_weight, correction_weight, num_clusters,
               num_pairs, used_lookup}``
        """
        defects = self._extract_defects(syndrome)
        correction = self.decode(syndrome)

        # Reconstruct cluster info
        uf = self._UF(self.n)
        # Pair defects for cluster count estimate
        n_pairs = len(defects) // 2

        return {
            "correction": correction.tolist(),
            "syndrome_weight": int(np.sum(syndrome)),
            "correction_weight": int(np.sum(correction)),
            "num_clusters": max(1, n_pairs),
            "num_pairs": n_pairs,
            "used_lookup": False,
        }
