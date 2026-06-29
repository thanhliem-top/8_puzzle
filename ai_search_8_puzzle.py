#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Search Algorithms Visualization for 8 Puzzle.

This project intentionally keeps all Python source in one file. The internal
architecture still uses small classes so the code remains understandable for
students and maintainable for future extension.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import itertools
import json
import math
import random
import sys
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception:  # pragma: no cover - self-test can run without a display.
    tk = None
    ttk = None
    filedialog = None
    messagebox = None


BOARD_SIZE = 3
BLANK = 0
DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
GOAL_STATES = {
    "Classic": DEFAULT_GOAL,
    "Spiral": (1, 2, 3, 8, 0, 4, 7, 6, 5),
    "Reverse": (8, 7, 6, 5, 4, 3, 2, 1, 0),
}

UNINFORMED_ALGORITHMS = [
    "Breadth First Search",
    "Depth First Search",
    "Depth Limited Search",
    "Iterative Deepening Search",
    "Uniform Cost Search",
]
INFORMED_ALGORITHMS = [
    "Greedy Best First Search",
    "A*",
]
GRAPH_ALGORITHMS = UNINFORMED_ALGORITHMS + INFORMED_ALGORITHMS
LOCAL_ALGORITHMS = [
    "Hill Climbing",
    "Local Beam Search",
    "Simulated Annealing",
]
COMPLEX_ENVIRONMENT_ALGORITHMS = [
    "AND-OR Search",
    "No Observation Search",
    "Partially Observable Search",
    "Online Search",
]
CSP_ALGORITHMS = [
    "Constraint Propagation",
    "Path Consistency",
    "Global Constraints",
    "Backtracking Search",
    "Min Conflicts",
    "Constraint Graph",
]
ADVERSARIAL_ALGORITHMS = [
    "Minimax",
    "Alpha Beta",
    "Expectimax",
]
EDUCATIONAL_ALGORITHMS = COMPLEX_ENVIRONMENT_ALGORITHMS + CSP_ALGORITHMS + ADVERSARIAL_ALGORITHMS
ALGORITHM_GROUPS = {
    "Uninformed Search": UNINFORMED_ALGORITHMS,
    "Informed Search": INFORMED_ALGORITHMS,
    "Local Search": LOCAL_ALGORITHMS,
    "Complex Environments": COMPLEX_ENVIRONMENT_ALGORITHMS,
    "Constraint Satisfaction": CSP_ALGORITHMS,
    "Adversarial Search": ADVERSARIAL_ALGORITHMS,
}
ALL_ALGORITHMS = GRAPH_ALGORITHMS + LOCAL_ALGORITHMS + EDUCATIONAL_ALGORITHMS
HEURISTICS = ["Manhattan Distance", "Misplaced Tiles", "Euclidean Distance"]

FONT_FAMILY = "Segoe UI"
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_PANEL_TITLE = (FONT_FAMILY, 14, "bold")
FONT_PAGE_TITLE = (FONT_FAMILY, 16, "bold")
FONT_GRID = (FONT_FAMILY, 13, "bold")
FONT_MONO = ("Consolas", 10)

THEME = {
    "bg": "#0b1120",
    "panel": "#111827",
    "panel2": "#243244",
    "control": "#0f1b2d",
    "border": "#475569",
    "text": "#f8fafc",
    "muted": "#cbd5e1",
    "accent": "#38bdf8",
    "accent2": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#fb7185",
    "solution": "#a3e635",
    "tile": "#1e293b",
    "tile_active": "#155e75",
}

ALGORITHM_FACTS = {
    "Breadth First Search": {
        "complete": "Yes",
        "optimal": "Yes, unit cost",
        "complexity": "Time O(b^d), Space O(b^d)",
    },
    "Depth First Search": {
        "complete": "No, unless bounded",
        "optimal": "No",
        "complexity": "Time O(b^m), Space O(bm)",
    },
    "Depth Limited Search": {
        "complete": "If goal within limit",
        "optimal": "No",
        "complexity": "Time O(b^l), Space O(bl)",
    },
    "Iterative Deepening Search": {
        "complete": "Yes",
        "optimal": "Yes, unit cost",
        "complexity": "Time O(b^d), Space O(bd)",
    },
    "Uniform Cost Search": {
        "complete": "Yes, positive cost",
        "optimal": "Yes",
        "complexity": "Time exponential, Space exponential",
    },
    "Greedy Best First Search": {
        "complete": "No in infinite spaces",
        "optimal": "No",
        "complexity": "Time exponential, Space exponential",
    },
    "A*": {
        "complete": "Yes",
        "optimal": "Yes, admissible h",
        "complexity": "Time exponential, Space exponential",
    },
    "Hill Climbing": {
        "complete": "No",
        "optimal": "No",
        "complexity": "Low memory, local optimum risk",
    },
    "Local Beam Search": {
        "complete": "No",
        "optimal": "No",
        "complexity": "O(kb) per iteration",
    },
    "Simulated Annealing": {
        "complete": "No practical guarantee",
        "optimal": "No practical guarantee",
        "complexity": "Depends on schedule",
    },
}


def compact_state(state: "PuzzleState | Tuple[int, ...]") -> str:
    tiles = state.tiles if isinstance(state, PuzzleState) else state
    rows = []
    for row in range(BOARD_SIZE):
        chunk = tiles[row * BOARD_SIZE : (row + 1) * BOARD_SIZE]
        rows.append("".join("_" if value == BLANK else str(value) for value in chunk))
    return "/".join(rows)


def safe_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


@dataclass(frozen=True)
class PuzzleState:
    tiles: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.tiles) != BOARD_SIZE * BOARD_SIZE:
            raise ValueError("A puzzle state must contain exactly 9 values.")

    @property
    def blank_index(self) -> int:
        return self.tiles.index(BLANK)

    def is_goal(self, goal: "PuzzleState") -> bool:
        return self.tiles == goal.tiles

    def neighbors(self) -> List[Tuple[str, "PuzzleState", int]]:
        blank = self.blank_index
        row, col = divmod(blank, BOARD_SIZE)
        moves = [
            ("Up", row > 0, -BOARD_SIZE),
            ("Down", row < BOARD_SIZE - 1, BOARD_SIZE),
            ("Left", col > 0, -1),
            ("Right", col < BOARD_SIZE - 1, 1),
        ]
        result: List[Tuple[str, PuzzleState, int]] = []
        for action, allowed, delta in moves:
            if not allowed:
                continue
            swap_index = blank + delta
            new_tiles = list(self.tiles)
            moved_tile = new_tiles[swap_index]
            new_tiles[blank], new_tiles[swap_index] = new_tiles[swap_index], new_tiles[blank]
            result.append((action, PuzzleState(tuple(new_tiles)), moved_tile))
        return result

    def as_rows(self) -> List[Tuple[int, int, int]]:
        return [
            self.tiles[row * BOARD_SIZE : (row + 1) * BOARD_SIZE]
            for row in range(BOARD_SIZE)
        ]


class PuzzleValidator:
    @staticmethod
    def parse(values: Sequence[str]) -> PuzzleState:
        try:
            numbers = tuple(int(value.strip()) for value in values)
        except ValueError as exc:
            raise ValueError("All cells must be integers from 0 to 8.") from exc
        if not PuzzleValidator.is_valid_tiles(numbers):
            raise ValueError("State must contain each number from 0 to 8 exactly once.")
        return PuzzleState(numbers)

    @staticmethod
    def is_valid_tiles(tiles: Sequence[int]) -> bool:
        return len(tiles) == 9 and sorted(tiles) == list(range(9))

    @staticmethod
    def inversion_parity_for_goal(state: PuzzleState, goal: PuzzleState) -> int:
        goal_order = {tile: index for index, tile in enumerate(goal.tiles) if tile != BLANK}
        sequence = [goal_order[tile] for tile in state.tiles if tile != BLANK]
        inversions = 0
        for left in range(len(sequence)):
            for right in range(left + 1, len(sequence)):
                if sequence[left] > sequence[right]:
                    inversions += 1
        return inversions % 2

    @staticmethod
    def is_solvable(state: PuzzleState, goal: PuzzleState) -> bool:
        return (
            PuzzleValidator.inversion_parity_for_goal(state, goal)
            == PuzzleValidator.inversion_parity_for_goal(goal, goal)
        )

    @staticmethod
    def shuffled_from(goal: PuzzleState, moves: int = 32) -> PuzzleState:
        state = goal
        previous: Optional[PuzzleState] = None
        for _ in range(moves):
            choices = [neighbor for neighbor in state.neighbors() if neighbor[1] != previous]
            action, next_state, _ = random.choice(choices)
            previous = state
            state = next_state
        return state


class HeuristicManager:
    @staticmethod
    def estimate(state: PuzzleState, goal: PuzzleState, name: str) -> float:
        if name == "Misplaced Tiles":
            return HeuristicManager.misplaced_tiles(state, goal)
        if name == "Euclidean Distance":
            return HeuristicManager.euclidean_distance(state, goal)
        return HeuristicManager.manhattan_distance(state, goal)

    @staticmethod
    def goal_positions(goal: PuzzleState) -> Dict[int, Tuple[int, int]]:
        return {
            tile: divmod(index, BOARD_SIZE)
            for index, tile in enumerate(goal.tiles)
            if tile != BLANK
        }

    @staticmethod
    def manhattan_distance(state: PuzzleState, goal: PuzzleState) -> float:
        positions = HeuristicManager.goal_positions(goal)
        total = 0
        for index, tile in enumerate(state.tiles):
            if tile == BLANK:
                continue
            row, col = divmod(index, BOARD_SIZE)
            goal_row, goal_col = positions[tile]
            total += abs(row - goal_row) + abs(col - goal_col)
        return float(total)

    @staticmethod
    def misplaced_tiles(state: PuzzleState, goal: PuzzleState) -> float:
        return float(
            sum(1 for index, tile in enumerate(state.tiles) if tile != BLANK and tile != goal.tiles[index])
        )

    @staticmethod
    def euclidean_distance(state: PuzzleState, goal: PuzzleState) -> float:
        positions = HeuristicManager.goal_positions(goal)
        total = 0.0
        for index, tile in enumerate(state.tiles):
            if tile == BLANK:
                continue
            row, col = divmod(index, BOARD_SIZE)
            goal_row, goal_col = positions[tile]
            total += math.sqrt((row - goal_row) ** 2 + (col - goal_col) ** 2)
        return total


_NODE_COUNTER = itertools.count(1)


@dataclass(eq=False)
class SearchNode:
    state: PuzzleState
    parent: Optional["SearchNode"] = None
    action: str = "Start"
    moved_tile: Optional[int] = None
    depth: int = 0
    cost: float = 0.0
    heuristic: float = 0.0
    score: float = 0.0
    children: List["SearchNode"] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(_NODE_COUNTER))

    def path(self) -> List["SearchNode"]:
        node: Optional[SearchNode] = self
        result: List[SearchNode] = []
        while node is not None:
            result.append(node)
            node = node.parent
        return list(reversed(result))

    def describe(self) -> str:
        f_value = self.cost + self.heuristic
        return (
            f"N{self.id} {compact_state(self.state)} "
            f"g={self.cost:.0f} h={self.heuristic:.1f} f={f_value:.1f}"
        )


@dataclass
class Metrics:
    execution_time: float = 0.0
    expanded_nodes: int = 0
    generated_nodes: int = 0
    frontier_size: int = 0
    explored_size: int = 0
    memory_kb: float = 0.0
    search_depth: int = 0
    max_depth: int = 0
    branching_factor: float = 0.0
    solution_length: int = 0
    total_cost: float = 0.0
    step_count: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "Execution Time": f"{self.execution_time:.4f}s",
            "Expanded Nodes": self.expanded_nodes,
            "Generated Nodes": self.generated_nodes,
            "Frontier Size": self.frontier_size,
            "Explored Size": self.explored_size,
            "Memory Usage": f"{self.memory_kb:.1f} KB",
            "Search Depth": self.search_depth,
            "Maximum Depth": self.max_depth,
            "Branching Factor": f"{self.branching_factor:.2f}",
            "Solution Length": self.solution_length,
            "Total Cost": f"{self.total_cost:.0f}",
            "Step Count": self.step_count,
        }


@dataclass
class StepSnapshot:
    step_index: int
    algorithm_name: str
    current_node: Optional[SearchNode]
    parent_node: Optional[SearchNode]
    children: List[SearchNode]
    removed_nodes: List[Tuple[SearchNode, str]]
    frontier: List[SearchNode]
    explored: List[SearchNode]
    visited_count: int
    open_list: List[str]
    closed_list: List[str]
    selected_reason: str
    explanation: str
    pseudocode_line: int
    status: str
    metrics: Metrics
    solution_path: List[SearchNode] = field(default_factory=list)

    def to_export_dict(self) -> Dict[str, Any]:
        node = self.current_node
        return {
            "step": self.step_index,
            "algorithm": self.algorithm_name,
            "status": self.status,
            "current_node": node.describe() if node else "",
            "parent": self.parent_node.describe() if self.parent_node else "",
            "children": [child.describe() for child in self.children],
            "removed": [f"{child.describe()} - {reason}" for child, reason in self.removed_nodes],
            "frontier": [node.describe() for node in self.frontier[:30]],
            "explored": [node.describe() for node in self.explored[-30:]],
            "explanation": self.explanation,
            "metrics": self.metrics.as_dict(),
            "solution_path": [compact_state(node.state) for node in self.solution_path],
        }


PSEUDOCODE = {
    "Breadth First Search": [
        "Create a FIFO queue and insert the start node.",
        "Remove the oldest node from the queue.",
        "If the node is goal, return the solution path.",
        "Put the node into explored.",
        "Generate all valid children.",
        "Insert unvisited children at the back of the queue.",
    ],
    "Depth First Search": [
        "Create a LIFO stack and insert the start node.",
        "Pop the newest node from the stack.",
        "If the node is goal, return the solution path.",
        "Put the node into explored.",
        "Generate all valid children.",
        "Push unvisited children onto the stack.",
    ],
    "Depth Limited Search": [
        "Create a stack and insert the start node.",
        "Pop the newest node from the stack.",
        "If the node is goal, return the solution path.",
        "If depth equals the limit, cut off this branch.",
        "Generate children and push unvisited nodes.",
    ],
    "Iterative Deepening Search": [
        "Set depth limit to 0.",
        "Run depth-limited search with the current limit.",
        "If goal is found, return the solution path.",
        "If cutoff occurs, increase the depth limit.",
        "Restart search from the initial state.",
    ],
    "Uniform Cost Search": [
        "Create a priority queue ordered by g(n).",
        "Remove the node with the smallest path cost g(n).",
        "If the node is goal, return the optimal path.",
        "Expand the node.",
        "Insert children if they improve known path cost.",
    ],
    "Greedy Best First Search": [
        "Create a priority queue ordered by h(n).",
        "Remove the node that appears closest to the goal.",
        "If the node is goal, return the path.",
        "Expand the node.",
        "Insert children using only heuristic priority.",
    ],
    "A*": [
        "Create a priority queue ordered by f(n)=g(n)+h(n).",
        "Remove the node with the smallest f(n).",
        "If the node is goal, return the optimal path.",
        "Expand the node.",
        "Insert children that improve the best known g(n).",
    ],
    "Hill Climbing": [
        "Start from the current state.",
        "Evaluate every neighbor with h(n).",
        "Move to the best neighbor if it improves h(n).",
        "Stop when the goal is reached or no improvement exists.",
    ],
    "Local Beam Search": [
        "Keep k best current states.",
        "Generate neighbors for all beam states.",
        "Select the k best successors by h(n).",
        "Stop when a goal state appears or progress stalls.",
    ],
    "Simulated Annealing": [
        "Start with a high temperature.",
        "Pick one random neighbor.",
        "Always accept better states.",
        "Sometimes accept worse states based on temperature.",
        "Cool the temperature and repeat.",
    ],
}

EDUCATIONAL_PSEUDOCODE = [
    "Map the 8 Puzzle state into the educational model.",
    "Identify what the algorithm would treat as states, choices, or constraints.",
    "Generate a small illustrative frontier.",
    "Explain the decision rule used by the algorithm.",
    "Show why this is a conceptual demo, not always a direct 8 Puzzle solver.",
]

EDUCATIONAL_NOTES = {
    "AND-OR Search": [
        "Treat each move as an OR choice and uncertain environment responses as AND requirements.",
        "A valid plan must solve every AND branch, not just one lucky path.",
        "This illustrates conditional planning rather than ordinary single-agent search.",
    ],
    "No Observation Search": [
        "The agent does not know the exact board, so it keeps a belief state.",
        "Actions transform a set of possible puzzle states at once.",
        "The goal is a policy that works for all states still possible.",
    ],
    "Partially Observable Search": [
        "Only part of the board is visible, so observations shrink the belief state.",
        "The demo shows how sensing changes the candidate state set.",
        "This is useful for learning belief updates.",
    ],
    "Online Search": [
        "The agent discovers neighbors only when it reaches a state.",
        "The demo records local exploration and backtracking decisions.",
        "This differs from offline search where the full transition model is known.",
    ],
    "Constraint Propagation": [
        "Each cell has a domain of possible tiles.",
        "All-different and fixed-position constraints remove impossible values.",
        "Propagation reduces the board before any search assignment.",
    ],
    "Path Consistency": [
        "Pairs of variables are checked against a third variable.",
        "Inconsistent tile-position combinations are removed.",
        "The demo uses the puzzle grid to visualize consistency filtering.",
    ],
    "Global Constraints": [
        "The all-different rule says each tile appears exactly once.",
        "The blank and numbered tiles form one global constraint over nine cells.",
        "The demo highlights why global constraints prune many invalid boards.",
    ],
    "Backtracking Search": [
        "Tiles are assigned to cells one by one.",
        "Invalid partial assignments are rejected immediately.",
        "This demonstrates CSP solving rather than move-based puzzle solving.",
    ],
    "Min Conflicts": [
        "Start with a complete but conflicting assignment.",
        "Change the variable causing the most conflict.",
        "Repeat until all constraints are satisfied or the limit is reached.",
    ],
    "Constraint Graph": [
        "Cells become variables and constraints become graph edges.",
        "The graph explains which assignments influence each other.",
        "This is a structural view of the puzzle as a CSP.",
    ],
    "Minimax": [
        "8 Puzzle is not normally adversarial, so the demo adds an opponent model.",
        "MAX tries to reduce heuristic distance; MIN tries to increase it.",
        "The tree explains best-worst decision making.",
    ],
    "Alpha Beta": [
        "Alpha beta keeps the same Minimax result while pruning useless branches.",
        "Alpha is MAX's best guarantee; beta is MIN's best guarantee.",
        "The demo marks branches that no longer affect the final choice.",
    ],
    "Expectimax": [
        "Chance nodes model random environment moves.",
        "The agent chooses the action with the best expected value.",
        "This is useful when outcomes are probabilistic, not adversarial.",
    ],
}


class SearchAlgorithm:
    def __init__(self, name: str, max_expansions: int = 10000) -> None:
        self.name = name
        self.max_expansions = max_expansions
        self.start: Optional[PuzzleState] = None
        self.goal: Optional[PuzzleState] = None
        self.heuristic_name = "Manhattan Distance"
        self.root: Optional[SearchNode] = None
        self.finished = False
        self.success = False
        self.status = "ready"
        self.metrics = Metrics()
        self.started_at = 0.0

    def initialize(self, start: PuzzleState, goal: PuzzleState, heuristic_name: str) -> None:
        self.start = start
        self.goal = goal
        self.heuristic_name = heuristic_name
        self.finished = False
        self.success = False
        self.status = "running"
        self.metrics = Metrics()
        self.started_at = time.perf_counter()
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def next_step(self) -> StepSnapshot:
        raise NotImplementedError

    def pseudocode(self) -> List[str]:
        return PSEUDOCODE.get(self.name, EDUCATIONAL_PSEUDOCODE)

    def _update_common_metrics(self, frontier_size: int, explored_size: int) -> None:
        self.metrics.execution_time = time.perf_counter() - self.started_at
        self.metrics.frontier_size = frontier_size
        self.metrics.explored_size = explored_size
        if self.metrics.expanded_nodes:
            self.metrics.branching_factor = (
                self.metrics.generated_nodes / self.metrics.expanded_nodes
            )
        if tracemalloc.is_tracing():
            _, peak = tracemalloc.get_traced_memory()
            self.metrics.memory_kb = peak / 1024


class GraphSearchAlgorithm(SearchAlgorithm):
    def __init__(
        self,
        name: str,
        mode: str,
        depth_limit: int = 20,
        max_expansions: int = 10000,
    ) -> None:
        super().__init__(name, max_expansions=max_expansions)
        self.mode = mode
        self.depth_limit = depth_limit
        self.frontier_queue: Deque[SearchNode] = deque()
        self.frontier_stack: List[SearchNode] = []
        self.frontier_heap: List[Tuple[float, int, SearchNode]] = []
        self.frontier_best: Dict[PuzzleState, float] = {}
        self.explored_cost: Dict[PuzzleState, float] = {}
        self.closed_nodes: List[SearchNode] = []
        self.tie_counter = itertools.count()

    def initialize(self, start: PuzzleState, goal: PuzzleState, heuristic_name: str) -> None:
        super().initialize(start, goal, heuristic_name)
        h_value = HeuristicManager.estimate(start, goal, heuristic_name)
        self.root = SearchNode(state=start, heuristic=h_value, score=self._score(0.0, h_value))
        self.frontier_queue = deque()
        self.frontier_stack = []
        self.frontier_heap = []
        self.frontier_best = {}
        self.explored_cost = {}
        self.closed_nodes = []
        self.tie_counter = itertools.count()
        self._push(self.root)

    def _score(self, cost: float, heuristic: float) -> float:
        if self.mode == "ucs":
            return cost
        if self.mode == "greedy":
            return heuristic
        if self.mode == "astar":
            return cost + heuristic
        return cost

    def _dominance_value(self, node: SearchNode) -> float:
        if self.mode == "greedy":
            return node.heuristic
        return node.cost

    def _push(self, node: SearchNode) -> None:
        self.frontier_best[node.state] = self._dominance_value(node)
        if self.mode == "bfs":
            self.frontier_queue.append(node)
        elif self.mode in {"dfs", "dls"}:
            self.frontier_stack.append(node)
        else:
            heapq.heappush(self.frontier_heap, (node.score, next(self.tie_counter), node))

    def _pop(self) -> Tuple[Optional[SearchNode], List[Tuple[SearchNode, str]]]:
        stale: List[Tuple[SearchNode, str]] = []
        while True:
            node: Optional[SearchNode]
            if self.mode == "bfs":
                if not self.frontier_queue:
                    return None, stale
                node = self.frontier_queue.popleft()
            elif self.mode in {"dfs", "dls"}:
                if not self.frontier_stack:
                    return None, stale
                node = self.frontier_stack.pop()
            else:
                if not self.frontier_heap:
                    return None, stale
                _, _, node = heapq.heappop(self.frontier_heap)

            best = self.frontier_best.get(node.state)
            if best is None:
                stale.append((node, "stale duplicate already replaced"))
                continue
            if abs(best - self._dominance_value(node)) > 1e-9:
                stale.append((node, "worse duplicate already replaced"))
                continue
            del self.frontier_best[node.state]
            return node, stale

    def _frontier_nodes(self) -> List[SearchNode]:
        if self.mode == "bfs":
            nodes = list(self.frontier_queue)
        elif self.mode in {"dfs", "dls"}:
            nodes = list(reversed(self.frontier_stack))
        else:
            nodes = [item[2] for item in sorted(self.frontier_heap, key=lambda item: (item[0], item[1]))]
        return [
            node
            for node in nodes
            if node.state in self.frontier_best
            and abs(self.frontier_best[node.state] - self._dominance_value(node)) <= 1e-9
        ]

    def _should_add(self, node: SearchNode) -> Tuple[bool, str]:
        explored_best = self.explored_cost.get(node.state)
        candidate = self._dominance_value(node)
        if explored_best is not None and explored_best <= node.cost:
            return False, "already explored with lower or equal cost"
        frontier_best = self.frontier_best.get(node.state)
        if frontier_best is not None and frontier_best <= candidate:
            return False, "frontier already has a better or equal candidate"
        return True, "accepted into frontier"

    def _selection_reason(self, node: SearchNode) -> str:
        if self.mode == "bfs":
            return "BFS uses a Queue, so the oldest frontier node is selected first."
        if self.mode == "dfs":
            return "DFS uses a Stack, so the newest frontier node is selected first."
        if self.mode == "dls":
            return f"DLS uses a Stack but cuts off nodes at depth {self.depth_limit}."
        if self.mode == "ucs":
            return f"UCS selects the smallest g(n). This node has g(n)={node.cost:.0f}."
        if self.mode == "greedy":
            return f"Greedy uses only h(n). This node has h(n)={node.heuristic:.1f}."
        if self.mode == "astar":
            return (
                "A* selects the smallest f(n)=g(n)+h(n). "
                f"Here f(n)={node.cost:.0f}+{node.heuristic:.1f}={node.score:.1f}."
            )
        return "The node is selected by the algorithm frontier rule."

    def next_step(self) -> StepSnapshot:
        assert self.goal is not None
        if self.finished:
            return self._terminal_snapshot("Algorithm already finished.", 0)

        self.metrics.step_count += 1
        node, stale_nodes = self._pop()
        if node is None:
            self.finished = True
            self.status = "failed"
            return self._snapshot(
                current_node=None,
                parent_node=None,
                children=[],
                removed_nodes=stale_nodes,
                selected_reason="Frontier is empty.",
                explanation="The frontier is empty, so no solution was found within the current limits.",
                pseudocode_line=1,
                status=self.status,
            )

        self.metrics.search_depth = node.depth
        self.metrics.max_depth = max(self.metrics.max_depth, node.depth)
        selected_reason = self._selection_reason(node)

        if node.state.is_goal(self.goal):
            self.finished = True
            self.success = True
            self.status = "solved"
            solution = node.path()
            self.metrics.solution_length = len(solution) - 1
            self.metrics.total_cost = node.cost
            return self._snapshot(
                current_node=node,
                parent_node=node.parent,
                children=[],
                removed_nodes=stale_nodes,
                selected_reason=selected_reason,
                explanation=(
                    f"Node {node.id} is the goal. The solution path has "
                    f"{self.metrics.solution_length} moves."
                ),
                pseudocode_line=2,
                status=self.status,
                solution_path=solution,
            )

        self.explored_cost[node.state] = node.cost
        self.closed_nodes.append(node)

        if self.mode == "dls" and node.depth >= self.depth_limit:
            return self._snapshot(
                current_node=node,
                parent_node=node.parent,
                children=[],
                removed_nodes=stale_nodes,
                selected_reason=selected_reason,
                explanation=(
                    f"Node {node.id} reached depth limit {self.depth_limit}. "
                    "The branch is cut off instead of expanded."
                ),
                pseudocode_line=3,
                status="cutoff",
            )

        if self.metrics.expanded_nodes >= self.max_expansions:
            self.finished = True
            self.status = "stopped"
            return self._snapshot(
                current_node=node,
                parent_node=node.parent,
                children=[],
                removed_nodes=stale_nodes,
                selected_reason=selected_reason,
                explanation=(
                    f"Safety limit reached after {self.max_expansions} expansions. "
                    "Try A*, a stronger heuristic, or a shallower initial state."
                ),
                pseudocode_line=4,
                status=self.status,
            )

        children: List[SearchNode] = []
        removed: List[Tuple[SearchNode, str]] = stale_nodes[:]
        for action, child_state, moved_tile in node.state.neighbors():
            child_h = HeuristicManager.estimate(child_state, self.goal, self.heuristic_name)
            child_cost = node.cost + 1
            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                moved_tile=moved_tile,
                depth=node.depth + 1,
                cost=child_cost,
                heuristic=child_h,
                score=self._score(child_cost, child_h),
            )
            node.children.append(child)
            children.append(child)
            self.metrics.generated_nodes += 1
            should_add, reason = self._should_add(child)
            if should_add:
                self._push(child)
            else:
                removed.append((child, reason))

        self.metrics.expanded_nodes += 1
        explanation = (
            f"Expanded node {node.id}. Generated {len(children)} children, "
            f"accepted {len(children) - len(removed) + len(stale_nodes)} into the frontier. "
            f"{selected_reason}"
        )
        return self._snapshot(
            current_node=node,
            parent_node=node.parent,
            children=children,
            removed_nodes=removed,
            selected_reason=selected_reason,
            explanation=explanation,
            pseudocode_line=4,
            status="running",
        )

    def _snapshot(
        self,
        current_node: Optional[SearchNode],
        parent_node: Optional[SearchNode],
        children: List[SearchNode],
        removed_nodes: List[Tuple[SearchNode, str]],
        selected_reason: str,
        explanation: str,
        pseudocode_line: int,
        status: str,
        solution_path: Optional[List[SearchNode]] = None,
    ) -> StepSnapshot:
        frontier = self._frontier_nodes()
        self._update_common_metrics(len(frontier), len(self.closed_nodes))
        open_list = [node.describe() for node in frontier[:40]]
        closed_list = [node.describe() for node in self.closed_nodes[-40:]]
        return StepSnapshot(
            step_index=self.metrics.step_count,
            algorithm_name=self.name,
            current_node=current_node,
            parent_node=parent_node,
            children=children,
            removed_nodes=removed_nodes,
            frontier=frontier,
            explored=self.closed_nodes[:],
            visited_count=len(self.frontier_best) + len(self.explored_cost),
            open_list=open_list,
            closed_list=closed_list,
            selected_reason=selected_reason,
            explanation=explanation,
            pseudocode_line=pseudocode_line,
            status=status,
            metrics=self.metrics,
            solution_path=solution_path or [],
        )

    def _terminal_snapshot(self, explanation: str, line: int) -> StepSnapshot:
        return self._snapshot(
            current_node=None,
            parent_node=None,
            children=[],
            removed_nodes=[],
            selected_reason="Finished.",
            explanation=explanation,
            pseudocode_line=line,
            status=self.status,
            solution_path=[],
        )


class IterativeDeepeningAlgorithm(GraphSearchAlgorithm):
    def __init__(self, max_depth: int = 32, max_expansions: int = 10000) -> None:
        super().__init__(
            "Iterative Deepening Search",
            mode="dls",
            depth_limit=0,
            max_expansions=max_expansions,
        )
        self.current_limit = 0
        self.max_depth = max_depth

    def initialize(self, start: PuzzleState, goal: PuzzleState, heuristic_name: str) -> None:
        self.current_limit = 0
        super().initialize(start, goal, heuristic_name)

    def _reset_iteration(self) -> None:
        assert self.start is not None and self.goal is not None
        h_value = HeuristicManager.estimate(self.start, self.goal, self.heuristic_name)
        self.root = SearchNode(
            state=self.start,
            heuristic=h_value,
            score=self._score(0.0, h_value),
        )
        self.frontier_stack = []
        self.frontier_queue = deque()
        self.frontier_heap = []
        self.frontier_best = {}
        self.explored_cost = {}
        self.closed_nodes = []
        self._push(self.root)

    def next_step(self) -> StepSnapshot:
        if self.finished:
            return self._terminal_snapshot("Algorithm already finished.", 0)
        if not self.frontier_stack and self.current_limit < self.max_depth:
            self.current_limit += 1
            self.depth_limit = self.current_limit
            self._reset_iteration()
            self.metrics.step_count += 1
            return self._snapshot(
                current_node=self.root,
                parent_node=None,
                children=[],
                removed_nodes=[],
                selected_reason=f"Increase depth limit to {self.current_limit}.",
                explanation=(
                    f"IDS finished the previous DLS pass without a solution. "
                    f"It restarts from the initial state with depth limit {self.current_limit}."
                ),
                pseudocode_line=3,
                status="new-depth-limit",
            )
        if self.current_limit >= self.max_depth and not self.frontier_stack:
            self.finished = True
            self.status = "failed"
            return self._snapshot(
                current_node=None,
                parent_node=None,
                children=[],
                removed_nodes=[],
                selected_reason="Maximum IDS limit reached.",
                explanation=f"IDS stopped after reaching maximum limit {self.max_depth}.",
                pseudocode_line=4,
                status=self.status,
            )
        return super().next_step()

    def _selection_reason(self, node: SearchNode) -> str:
        return (
            f"IDS is currently running DLS with limit {self.current_limit}. "
            "Within this pass it uses a Stack."
        )


class LocalSearchAlgorithm(SearchAlgorithm):
    def __init__(self, name: str, beam_width: int = 3, max_iterations: int = 600) -> None:
        super().__init__(name, max_expansions=max_iterations)
        self.beam_width = beam_width
        self.max_iterations = max_iterations
        self.current: Optional[SearchNode] = None
        self.beam: List[SearchNode] = []
        self.path_nodes: List[SearchNode] = []
        self.visited: set[PuzzleState] = set()
        self.temperature = 10.0
        self.cooling = 0.96

    def initialize(self, start: PuzzleState, goal: PuzzleState, heuristic_name: str) -> None:
        super().initialize(start, goal, heuristic_name)
        h_value = HeuristicManager.estimate(start, goal, heuristic_name)
        self.root = SearchNode(state=start, heuristic=h_value, score=h_value)
        self.current = self.root
        self.beam = [self.root]
        self.path_nodes = [self.root]
        self.visited = {start}
        self.temperature = 10.0

    def next_step(self) -> StepSnapshot:
        assert self.goal is not None
        if self.finished:
            return self._snapshot("Algorithm already finished.", 0, "finished", [], [])
        self.metrics.step_count += 1
        if self.name == "Hill Climbing":
            return self._hill_step()
        if self.name == "Local Beam Search":
            return self._beam_step()
        return self._annealing_step()

    def _make_child(self, parent: SearchNode, action: str, state: PuzzleState, moved: int) -> SearchNode:
        assert self.goal is not None
        h_value = HeuristicManager.estimate(state, self.goal, self.heuristic_name)
        return SearchNode(
            state=state,
            parent=parent,
            action=action,
            moved_tile=moved,
            depth=parent.depth + 1,
            cost=parent.cost + 1,
            heuristic=h_value,
            score=h_value,
        )

    def _hill_step(self) -> StepSnapshot:
        assert self.current is not None and self.goal is not None
        if self.current.state.is_goal(self.goal):
            return self._finish_success(self.current, "Current node is already the goal.")

        children = [
            self._make_child(self.current, action, state, moved)
            for action, state, moved in self.current.state.neighbors()
        ]
        self.current.children.extend(children)
        self.metrics.generated_nodes += len(children)
        self.metrics.expanded_nodes += 1
        best = min(children, key=lambda node: node.heuristic)
        removed = [(child, "not the steepest improvement") for child in children if child is not best]

        if best.heuristic < self.current.heuristic and best.state not in self.visited:
            previous_h = self.current.heuristic
            self.current = best
            self.path_nodes.append(best)
            self.visited.add(best.state)
            if best.state.is_goal(self.goal):
                return self._finish_success(
                    best,
                    f"Hill Climbing moved from h={previous_h:.1f} to h=0 and reached the goal.",
                    children,
                    removed,
                )
            return self._snapshot(
                explanation=(
                    f"Hill Climbing chose node {best.id} because it has the lowest "
                    f"h(n)={best.heuristic:.1f}, improving from {previous_h:.1f}."
                ),
                line=2,
                status="running",
                children=children,
                removed=removed,
            )

        self.finished = True
        self.status = "local-optimum"
        return self._snapshot(
            explanation=(
                f"No neighbor improves h(n)={self.current.heuristic:.1f}. "
                "The search stops at a local optimum."
            ),
            line=3,
            status=self.status,
            children=children,
            removed=removed + [(best, "best neighbor does not improve the current state")],
        )

    def _beam_step(self) -> StepSnapshot:
        assert self.goal is not None
        all_children: List[SearchNode] = []
        for parent in self.beam:
            if parent.state.is_goal(self.goal):
                return self._finish_success(parent, "A beam node is the goal.")
            for action, state, moved in parent.state.neighbors():
                child = self._make_child(parent, action, state, moved)
                parent.children.append(child)
                if child.state not in self.visited:
                    all_children.append(child)

        self.metrics.generated_nodes += len(all_children)
        self.metrics.expanded_nodes += len(self.beam)
        if not all_children:
            self.finished = True
            self.status = "stalled"
            return self._snapshot(
                "Local Beam Search has no unseen successors left.",
                3,
                self.status,
                [],
                [],
            )

        ranked = sorted(all_children, key=lambda node: node.heuristic)
        selected = ranked[: self.beam_width]
        removed = [(node, "outside top-k beam") for node in ranked[self.beam_width :]]
        for node in selected:
            self.visited.add(node.state)
        self.beam = selected
        self.current = selected[0]
        self.path_nodes.append(self.current)
        goal_node = next((node for node in selected if node.state.is_goal(self.goal)), None)
        if goal_node:
            return self._finish_success(
                goal_node,
                f"Local Beam Search found a goal among the top {self.beam_width} successors.",
                all_children,
                removed,
            )
        return self._snapshot(
            explanation=(
                f"Generated {len(all_children)} successors and kept the best "
                f"{len(selected)} states by h(n)."
            ),
            line=2,
            status="running",
            children=all_children,
            removed=removed,
        )

    def _annealing_step(self) -> StepSnapshot:
        assert self.current is not None and self.goal is not None
        if self.current.state.is_goal(self.goal):
            return self._finish_success(self.current, "Current node is already the goal.")
        if self.metrics.step_count > self.max_iterations or self.temperature < 0.03:
            self.finished = True
            self.status = "cooled"
            return self._snapshot(
                "Temperature is too low or iteration limit reached, so annealing stops.",
                4,
                self.status,
                [],
                [],
            )

        children = [
            self._make_child(self.current, action, state, moved)
            for action, state, moved in self.current.state.neighbors()
        ]
        self.current.children.extend(children)
        self.metrics.generated_nodes += len(children)
        self.metrics.expanded_nodes += 1
        candidate = random.choice(children)
        delta = candidate.heuristic - self.current.heuristic
        probability = 1.0 if delta <= 0 else math.exp(-delta / max(self.temperature, 0.001))
        accepted = random.random() < probability
        removed = [(child, "random neighbor not sampled") for child in children if child is not candidate]
        if accepted:
            old = self.current
            self.current = candidate
            self.path_nodes.append(candidate)
            self.visited.add(candidate.state)
            decision = (
                f"Accepted node {candidate.id}. Δh={delta:.1f}, "
                f"T={self.temperature:.2f}, probability={safe_percent(probability)}."
            )
            if candidate.state.is_goal(self.goal):
                return self._finish_success(candidate, decision + " The goal was reached.", children, removed)
            line = 2 if candidate.heuristic <= old.heuristic else 3
        else:
            removed.append((candidate, "rejected by annealing probability"))
            decision = (
                f"Rejected node {candidate.id}. Δh={delta:.1f}, "
                f"T={self.temperature:.2f}, probability={safe_percent(probability)}."
            )
            line = 3

        self.temperature *= self.cooling
        return self._snapshot(decision, line, "running", children, removed)

    def _finish_success(
        self,
        node: SearchNode,
        explanation: str,
        children: Optional[List[SearchNode]] = None,
        removed: Optional[List[Tuple[SearchNode, str]]] = None,
    ) -> StepSnapshot:
        self.finished = True
        self.success = True
        self.status = "solved"
        solution = node.path()
        self.metrics.solution_length = len(solution) - 1
        self.metrics.total_cost = node.cost
        return self._snapshot(explanation, 3, self.status, children or [], removed or [], solution)

    def _snapshot(
        self,
        explanation: str,
        line: int,
        status: str,
        children: List[SearchNode],
        removed: List[Tuple[SearchNode, str]],
        solution: Optional[List[SearchNode]] = None,
    ) -> StepSnapshot:
        current = self.current
        frontier = self.beam if self.name == "Local Beam Search" else children
        explored = self.path_nodes[:]
        self.metrics.search_depth = current.depth if current else 0
        self.metrics.max_depth = max(self.metrics.max_depth, self.metrics.search_depth)
        self._update_common_metrics(len(frontier), len(explored))
        return StepSnapshot(
            step_index=self.metrics.step_count,
            algorithm_name=self.name,
            current_node=current,
            parent_node=current.parent if current else None,
            children=children,
            removed_nodes=removed,
            frontier=frontier,
            explored=explored,
            visited_count=len(self.visited),
            open_list=[node.describe() for node in frontier[:40]],
            closed_list=[node.describe() for node in explored[-40:]],
            selected_reason=(
                "Local search chooses states by heuristic quality instead of global graph optimality."
            ),
            explanation=explanation,
            pseudocode_line=line,
            status=status,
            metrics=self.metrics,
            solution_path=solution or [],
        )


class EducationalAlgorithm(SearchAlgorithm):
    def __init__(self, name: str) -> None:
        super().__init__(name, max_expansions=20)
        self.stage = 0
        self.notes: List[str] = EDUCATIONAL_NOTES.get(name, [])
        self.demo_nodes: List[SearchNode] = []

    def initialize(self, start: PuzzleState, goal: PuzzleState, heuristic_name: str) -> None:
        super().initialize(start, goal, heuristic_name)
        h_value = HeuristicManager.estimate(start, goal, heuristic_name)
        self.root = SearchNode(state=start, heuristic=h_value, score=h_value)
        self.demo_nodes = [self.root]
        self.stage = 0

    def pseudocode(self) -> List[str]:
        return EDUCATIONAL_PSEUDOCODE

    def next_step(self) -> StepSnapshot:
        assert self.root is not None and self.goal is not None
        if self.finished:
            return self._snapshot("Educational demo already finished.", 4, "finished", [])

        self.metrics.step_count += 1
        self.stage += 1
        children: List[SearchNode] = []
        if self.stage == 3:
            for action, state, moved in self.root.state.neighbors()[:3]:
                h_value = HeuristicManager.estimate(state, self.goal, self.heuristic_name)
                child = SearchNode(
                    state=state,
                    parent=self.root,
                    action=action,
                    moved_tile=moved,
                    depth=1,
                    cost=1,
                    heuristic=h_value,
                    score=h_value,
                )
                self.root.children.append(child)
                children.append(child)
            self.demo_nodes.extend(children)
            self.metrics.generated_nodes += len(children)
            self.metrics.expanded_nodes += 1

        if self.stage >= 5:
            self.finished = True
            self.status = "demo-complete"

        note = self.notes[(self.stage - 1) % len(self.notes)] if self.notes else ""
        explanation = (
            f"{self.name}: {note} "
            "This panel is an educational presentation because the standard 8 Puzzle is "
            "a deterministic single-agent search problem."
        )
        return self._snapshot(explanation, min(self.stage - 1, 4), self.status, children)

    def _snapshot(
        self,
        explanation: str,
        line: int,
        status: str,
        children: List[SearchNode],
    ) -> StepSnapshot:
        assert self.root is not None
        current = children[0] if children else self.root
        self.metrics.search_depth = current.depth
        self.metrics.max_depth = max(self.metrics.max_depth, current.depth)
        self._update_common_metrics(len(children), len(self.demo_nodes))
        return StepSnapshot(
            step_index=self.metrics.step_count,
            algorithm_name=self.name,
            current_node=current,
            parent_node=current.parent,
            children=children,
            removed_nodes=[],
            frontier=children,
            explored=self.demo_nodes[:],
            visited_count=len(self.demo_nodes),
            open_list=[node.describe() for node in children],
            closed_list=[node.describe() for node in self.demo_nodes[-20:]],
            selected_reason="Educational demo step.",
            explanation=explanation,
            pseudocode_line=line,
            status=status,
            metrics=self.metrics,
            solution_path=[],
        )


def create_algorithm(name: str, max_expansions: int = 10000) -> SearchAlgorithm:
    mapping = {
        "Breadth First Search": ("bfs", 0),
        "Depth First Search": ("dfs", 0),
        "Depth Limited Search": ("dls", 20),
        "Uniform Cost Search": ("ucs", 0),
        "Greedy Best First Search": ("greedy", 0),
        "A*": ("astar", 0),
    }
    if name == "Iterative Deepening Search":
        return IterativeDeepeningAlgorithm(max_expansions=max_expansions)
    if name in mapping:
        mode, limit = mapping[name]
        return GraphSearchAlgorithm(
            name=name,
            mode=mode,
            depth_limit=limit or 20,
            max_expansions=max_expansions,
        )
    if name in LOCAL_ALGORITHMS:
        return LocalSearchAlgorithm(name)
    return EducationalAlgorithm(name)


class SearchEngine:
    def __init__(self) -> None:
        self.algorithm: Optional[SearchAlgorithm] = None
        self.history: List[StepSnapshot] = []
        self.display_index = -1
        self.config: Tuple[PuzzleState, PuzzleState, str, str] | None = None

    def configure(
        self,
        start: PuzzleState,
        goal: PuzzleState,
        algorithm_name: str,
        heuristic_name: str,
    ) -> None:
        self.algorithm = create_algorithm(algorithm_name)
        self.algorithm.initialize(start, goal, heuristic_name)
        self.history = []
        self.display_index = -1
        self.config = (start, goal, algorithm_name, heuristic_name)

    def step(self) -> StepSnapshot:
        if self.algorithm is None:
            raise RuntimeError("Search engine is not configured.")
        if self.display_index < len(self.history) - 1:
            self.display_index += 1
            return self.history[self.display_index]
        snapshot = self.algorithm.next_step()
        self.history.append(snapshot)
        self.display_index = len(self.history) - 1
        return snapshot

    def undo(self) -> Optional[StepSnapshot]:
        if not self.history:
            return None
        self.display_index = max(0, self.display_index - 1)
        return self.history[self.display_index]

    def redo(self) -> Optional[StepSnapshot]:
        if not self.history:
            return None
        self.display_index = min(len(self.history) - 1, self.display_index + 1)
        return self.history[self.display_index]

    def current_snapshot(self) -> Optional[StepSnapshot]:
        if self.display_index < 0 or not self.history:
            return None
        return self.history[self.display_index]

    def export_payload(self) -> Dict[str, Any]:
        start, goal, algorithm_name, heuristic_name = self.config or (
            PuzzleState(DEFAULT_GOAL),
            PuzzleState(DEFAULT_GOAL),
            "",
            "",
        )
        latest = self.current_snapshot()
        return {
            "project": "AI Search Algorithms Visualization for 8 Puzzle",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "algorithm": algorithm_name,
            "heuristic": heuristic_name,
            "initial_state": compact_state(start),
            "goal_state": compact_state(goal),
            "final_status": latest.status if latest else "not-started",
            "metrics": latest.metrics.as_dict() if latest else {},
            "steps": [snapshot.to_export_dict() for snapshot in self.history],
        }


class PuzzleBoardView:
    def __init__(self, parent: tk.Widget, size: int = 300) -> None:
        self.size = size
        self.canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.state = PuzzleState(DEFAULT_GOAL)

    def draw(self, state: PuzzleState, highlight: Optional[int] = None) -> None:
        self.state = state
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), self.size)
        height = max(self.canvas.winfo_height(), self.size)
        side = min(width, height) - 24
        cell = side / BOARD_SIZE
        left = (width - side) / 2
        top = (height - side) / 2
        for index, tile in enumerate(state.tiles):
            row, col = divmod(index, BOARD_SIZE)
            x1 = left + col * cell
            y1 = top + row * cell
            x2 = x1 + cell - 8
            y2 = y1 + cell - 8
            fill = THEME["panel2"] if tile == BLANK else THEME["tile"]
            if highlight == index and tile != BLANK:
                fill = THEME["tile_active"]
            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill,
                outline=THEME["accent"],
                width=2,
            )
            if tile != BLANK:
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=str(tile),
                    fill=THEME["text"],
                    font=(FONT_FAMILY, int(cell * 0.36), "bold"),
                )


class SearchTreeView:
    def __init__(self, parent: tk.Widget) -> None:
        self.zoom = 1.0
        wrapper = tk.Frame(parent, bg=THEME["panel"])
        wrapper.pack(fill="both", expand=True)
        controls = tk.Frame(wrapper, bg=THEME["panel"])
        controls.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(controls, text="+", command=self.zoom_in, **button_style()).pack(side="left", padx=2)
        tk.Button(controls, text="-", command=self.zoom_out, **button_style()).pack(side="left", padx=2)
        tk.Button(controls, text="Reset Zoom", command=self.reset_zoom, **button_style()).pack(side="left", padx=2)
        self.canvas = tk.Canvas(
            wrapper,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.last_args: Tuple[Any, ...] = tuple()

    def zoom_in(self) -> None:
        self.zoom = min(2.2, self.zoom + 0.15)
        self.redraw()

    def zoom_out(self) -> None:
        self.zoom = max(0.55, self.zoom - 0.15)
        self.redraw()

    def reset_zoom(self) -> None:
        self.zoom = 1.0
        self.redraw()

    def redraw(self) -> None:
        if self.last_args:
            self.draw(*self.last_args)

    def draw(
        self,
        root: Optional[SearchNode],
        current: Optional[SearchNode],
        frontier: Sequence[SearchNode],
        explored: Sequence[SearchNode],
        solution: Sequence[SearchNode],
        removed: Sequence[Tuple[SearchNode, str]],
    ) -> None:
        self.last_args = (root, current, frontier, explored, solution, removed)
        self.canvas.delete("all")
        if root is None:
            self.canvas.create_text(
                20,
                20,
                text="Search tree will appear after the first step.",
                anchor="nw",
                fill=THEME["muted"],
                font=(FONT_FAMILY, 11),
            )
            return

        frontier_states = {node.state for node in frontier}
        explored_states = {node.state for node in explored}
        solution_states = {node.state for node in solution}
        removed_states = {node.state for node, _ in removed}
        current_id = current.id if current else None

        nodes: List[SearchNode] = []
        queue: Deque[SearchNode] = deque([root])
        seen_ids: set[int] = set()
        while queue and len(nodes) < 150:
            node = queue.popleft()
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)
            nodes.append(node)
            queue.extend(node.children)

        levels: Dict[int, List[SearchNode]] = defaultdict(list)
        for node in nodes:
            levels[node.depth].append(node)
        positions: Dict[int, Tuple[float, float]] = {}
        x_gap = 112 * self.zoom
        y_gap = 92 * self.zoom
        radius = 27 * self.zoom
        for depth, level_nodes in levels.items():
            for index, node in enumerate(level_nodes):
                x = 70 * self.zoom + index * x_gap
                y = 55 * self.zoom + depth * y_gap
                positions[node.id] = (x, y)

        for node in nodes:
            if node.parent and node.parent.id in positions and node.id in positions:
                x1, y1 = positions[node.parent.id]
                x2, y2 = positions[node.id]
                self.canvas.create_line(x1, y1 + radius, x2, y2 - radius, fill=THEME["border"], width=2)

        for node in nodes:
            x, y = positions[node.id]
            fill = THEME["panel2"]
            outline = THEME["border"]
            if node.state in explored_states:
                fill = "#273449"
            if node.state in frontier_states:
                outline = THEME["accent"]
            if node.state in removed_states:
                outline = THEME["danger"]
            if node.state in solution_states:
                fill = "#365314"
                outline = THEME["solution"]
            if node.id == current_id:
                fill = "#164e63"
                outline = THEME["accent"]
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=fill,
                outline=outline,
                width=2,
            )
            label = f"N{node.id}\n{compact_state(node.state)}\ng={node.cost:.0f} h={node.heuristic:.0f}"
            self.canvas.create_text(
                x,
                y,
                text=label,
                fill=THEME["text"],
                font=(FONT_FAMILY, max(6, int(7 * self.zoom))),
            )

        max_x = max((pos[0] for pos in positions.values()), default=600) + 140
        max_y = max((pos[1] for pos in positions.values()), default=400) + 140
        self.canvas.configure(scrollregion=(0, 0, max_x, max_y))


class StatsPanel:
    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.LabelFrame(
            parent,
            text="Statistics",
            bg=THEME["panel"],
            fg=THEME["text"],
            bd=1,
            relief="solid",
            labelanchor="n",
            font=FONT_BODY_BOLD,
        )
        self.frame.pack(fill="both", expand=False, padx=8, pady=8)
        self.labels: Dict[str, tk.Label] = {}
        for row, key in enumerate(Metrics().as_dict().keys()):
            name = tk.Label(self.frame, text=key, anchor="w", bg=THEME["panel"], fg=THEME["muted"], font=FONT_BODY)
            value = tk.Label(self.frame, text="-", anchor="e", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD)
            name.grid(row=row, column=0, sticky="ew", padx=8, pady=2)
            value.grid(row=row, column=1, sticky="ew", padx=8, pady=2)
            self.labels[key] = value
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

    def update(self, metrics: Metrics) -> None:
        for key, value in metrics.as_dict().items():
            self.labels[key].configure(text=str(value))


class TextPanel:
    def __init__(self, parent: tk.Widget, title: str, height: int = 9) -> None:
        self.frame = tk.LabelFrame(
            parent,
            text=title,
            bg=THEME["panel"],
            fg=THEME["text"],
            bd=1,
            relief="solid",
            labelanchor="n",
            font=FONT_BODY_BOLD,
        )
        self.text = tk.Text(
            self.frame,
            height=height,
            bg="#07111f",
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            wrap="word",
            font=FONT_MONO,
            selectbackground=THEME["accent"],
            selectforeground="#001018",
        )
        self.text.pack(fill="both", expand=True, padx=6, pady=6)
        self.text.tag_configure("active", background="#0e7490", foreground="#ffffff")
        self.text.tag_configure("muted", foreground=THEME["muted"])
        self.text.configure(state="disabled")

    def set(self, content: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.configure(state="disabled")

    def append(self, content: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", content + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def set_pseudocode(self, lines: Sequence[str], active_line: int) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for index, line in enumerate(lines):
            prefix = ">> " if index == active_line else "   "
            start = self.text.index("end")
            self.text.insert("end", f"{prefix}{index + 1}. {line}\n")
            end = self.text.index("end")
            if index == active_line:
                self.text.tag_add("active", start, end)
        self.text.configure(state="disabled")


class ComparePanel:
    def __init__(self, parent: tk.Widget, app: "VisualizationApp") -> None:
        self.app = app
        self.frame = tk.Frame(parent, bg=THEME["bg"])
        self.frame.pack(fill="both", expand=True)
        header = tk.Frame(self.frame, bg=THEME["bg"])
        header.pack(fill="x", padx=10, pady=10)
        tk.Label(
            header,
            text="Compare Algorithms",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=FONT_PAGE_TITLE,
        ).pack(side="left")
        tk.Button(header, text="Run Compare", command=self.run_compare, **button_style()).pack(side="right")

        options = tk.Frame(self.frame, bg=THEME["panel"])
        options.pack(fill="x", padx=10, pady=(0, 10))
        self.vars: Dict[str, tk.BooleanVar] = {}
        defaults = {"Breadth First Search", "Uniform Cost Search", "Greedy Best First Search", "A*", "Hill Climbing"}
        for group_name in ["Uninformed Search", "Informed Search", "Local Search"]:
            group_box = tk.LabelFrame(
                options,
                text=group_name,
                bg=THEME["panel"],
                fg=THEME["text"],
                bd=1,
                relief="solid",
                labelanchor="n",
                font=FONT_BODY_BOLD,
            )
            group_box.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            for algorithm in ALGORITHM_GROUPS[group_name]:
                var = tk.BooleanVar(value=algorithm in defaults)
                self.vars[algorithm] = var
                tk.Checkbutton(
                    group_box,
                    text=algorithm,
                    variable=var,
                    bg=THEME["panel"],
                    fg=THEME["text"],
                    selectcolor=THEME["control"],
                    activebackground=THEME["panel"],
                    activeforeground=THEME["accent"],
                    font=FONT_BODY,
                    anchor="w",
                ).pack(fill="x", padx=8, pady=3)

        columns = ("algorithm", "time", "memory", "nodes", "length", "optimal", "complete", "complexity", "status")
        self.table = ttk.Treeview(self.frame, columns=columns, show="headings", height=14)
        headings = {
            "algorithm": "Algorithm",
            "time": "Time",
            "memory": "Memory",
            "nodes": "Nodes",
            "length": "Solution",
            "optimal": "Optimal",
            "complete": "Complete",
            "complexity": "Complexity",
            "status": "Status",
        }
        widths = {
            "algorithm": 190,
            "time": 90,
            "memory": 95,
            "nodes": 85,
            "length": 85,
            "optimal": 130,
            "complete": 130,
            "complexity": 210,
            "status": 100,
        }
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=widths[column], anchor="w")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.summary = TextPanel(self.frame, "Comparison Notes", height=6)
        self.summary.frame.pack(fill="x", padx=10, pady=(0, 10))

    def run_compare(self) -> None:
        selected = [name for name, var in self.vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Compare", "Select at least one algorithm.")
            return
        start, goal = self.app.read_start_goal()
        heuristic = self.app.heuristic_var.get()
        for row in self.table.get_children():
            self.table.delete(row)

        records = []
        for name in selected:
            record = run_algorithm_for_compare(name, start, goal, heuristic, max_steps=6000)
            records.append(record)
            facts = ALGORITHM_FACTS.get(name, {})
            self.table.insert(
                "",
                "end",
                values=(
                    name,
                    f"{record['time']:.3f}s",
                    f"{record['memory']:.1f} KB",
                    record["nodes"],
                    record["solution_length"],
                    facts.get("optimal", "Demo"),
                    facts.get("complete", "Demo"),
                    facts.get("complexity", "Educational"),
                    record["status"],
                ),
            )

        solved = [record for record in records if record["status"] == "solved"]
        if solved:
            fastest = min(solved, key=lambda item: item["time"])
            smallest = min(solved, key=lambda item: item["nodes"])
            note = (
                f"Fastest solved run: {fastest['algorithm']} in {fastest['time']:.3f}s.\n"
                f"Fewest expanded nodes: {smallest['algorithm']} with {smallest['nodes']} nodes.\n"
                "Use the Solver tab to inspect the exact step-by-step reasoning."
            )
        else:
            note = "No selected algorithm solved within the safety limit. Try an easier shuffled state or A*."
        self.summary.set(note)


class EducationalDemoPanel:
    def __init__(self, parent: tk.Widget, app: "VisualizationApp") -> None:
        self.app = app
        self.frame = tk.Frame(parent, bg=THEME["bg"])
        self.frame.pack(fill="both", expand=True)
        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=10, pady=10)
        tk.Label(
            top,
            text="Educational Demo",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=FONT_PAGE_TITLE,
        ).pack(side="left")
        self.algorithm_var = tk.StringVar(value=EDUCATIONAL_ALGORITHMS[0])
        combo = ttk.Combobox(top, textvariable=self.algorithm_var, values=EDUCATIONAL_ALGORITHMS, width=30, state="readonly")
        combo.pack(side="left", padx=12)
        tk.Button(top, text="Load In Solver", command=self.load_in_solver, **button_style()).pack(side="left", padx=4)
        tk.Button(top, text="Preview Step", command=self.preview_step, **button_style()).pack(side="left", padx=4)

        body = tk.Frame(self.frame, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=10)
        self.board = PuzzleBoardView(body, size=260)
        self.info = TextPanel(body, "Concept Explanation", height=18)
        self.info.frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.demo_algorithm: Optional[SearchAlgorithm] = None
        self.refresh_info()
        combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_info())

    def refresh_info(self) -> None:
        name = self.algorithm_var.get()
        notes = EDUCATIONAL_NOTES.get(name, [])
        content = f"{name}\n\n" + "\n".join(f"- {note}" for note in notes)
        content += (
            "\n\nThis mode uses the 8 Puzzle board as a teaching object. "
            "If the algorithm is not a natural direct solver for 8 Puzzle, the app clearly marks it as a demo."
        )
        self.info.set(content)
        self.demo_algorithm = None

    def load_in_solver(self) -> None:
        self.app.set_solver_algorithm(self.algorithm_var.get())
        self.app.notebook.select(self.app.solver_tab)

    def preview_step(self) -> None:
        start, goal = self.app.read_start_goal()
        if self.demo_algorithm is None:
            self.demo_algorithm = EducationalAlgorithm(self.algorithm_var.get())
            self.demo_algorithm.initialize(start, goal, self.app.heuristic_var.get())
        snapshot = self.demo_algorithm.next_step()
        self.board.draw(snapshot.current_node.state if snapshot.current_node else start)
        self.info.set(snapshot.explanation)


def button_style() -> Dict[str, Any]:
    return {
        "bg": THEME["panel2"],
        "fg": THEME["text"],
        "activebackground": THEME["accent"],
        "activeforeground": "#001018",
        "relief": "flat",
        "bd": 0,
        "padx": 9,
        "pady": 5,
        "font": FONT_BODY_BOLD,
    }


class VisualizationApp:
    def __init__(self) -> None:
        if tk is None:
            raise RuntimeError("tkinter is required to run the GUI.")
        self.root = tk.Tk()
        self.root.title("AI Search Algorithms Visualization for 8 Puzzle")
        self.root.geometry("1500x920")
        self.root.minsize(1160, 760)
        self.root.configure(bg=THEME["bg"])
        self.configure_style()

        self.engine = SearchEngine()
        self.running = False
        self.after_id: Optional[str] = None
        self.algorithm_group_var = tk.StringVar(value="Informed Search")
        self.algorithm_var = tk.StringVar(value="A*")
        self.heuristic_var = tk.StringVar(value="Manhattan Distance")
        self.goal_var = tk.StringVar(value="Classic")
        self.speed_var = tk.IntVar(value=55)
        self.entries: List[tk.Entry] = []
        self.goal_entries: List[tk.Entry] = []
        self.current_start = PuzzleState((1, 2, 3, 4, 5, 6, 0, 7, 8))
        self.current_goal = PuzzleState(GOAL_STATES[self.goal_var.get()])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.solver_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        self.compare_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        self.education_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        self.notebook.add(self.solver_tab, text="Solver")
        self.notebook.add(self.compare_tab, text="Compare")
        self.notebook.add(self.education_tab, text="Educational Demo")

        self.build_solver_tab()
        self.compare_panel = ComparePanel(self.compare_tab, self)
        self.education_panel = EducationalDemoPanel(self.education_tab, self)
        self.reset_engine()

    def configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.root.option_add("*Font", FONT_BODY)
        self.root.option_add("*TCombobox*Listbox.font", FONT_BODY)
        self.root.option_add("*TCombobox*Listbox.background", "#0f172a")
        self.root.option_add("*TCombobox*Listbox.foreground", THEME["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", THEME["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#001018")
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 8), background=THEME["panel2"], foreground=THEME["text"], font=FONT_BODY_BOLD)
        style.map("TNotebook.Tab", background=[("selected", THEME["accent"])], foreground=[("selected", "#001018")])
        style.configure("Treeview", background="#020617", foreground=THEME["text"], fieldbackground="#020617", rowheight=30, font=FONT_BODY)
        style.configure("Treeview.Heading", background=THEME["panel2"], foreground=THEME["text"], font=FONT_BODY_BOLD)
        style.map("Treeview", background=[("selected", THEME["accent"])], foreground=[("selected", "#001018")])
        style.configure(
            "TCombobox",
            fieldbackground=THEME["control"],
            background=THEME["panel2"],
            foreground=THEME["text"],
            arrowcolor=THEME["accent"],
            bordercolor=THEME["border"],
            lightcolor=THEME["border"],
            darkcolor=THEME["border"],
            padding=(8, 4),
            font=FONT_BODY,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", THEME["control"])],
            foreground=[("readonly", THEME["text"])],
            selectbackground=[("readonly", THEME["control"])],
            selectforeground=[("readonly", THEME["text"])],
        )

    def algorithms_for_current_group(self) -> List[str]:
        return ALGORITHM_GROUPS.get(self.algorithm_group_var.get(), INFORMED_ALGORITHMS)

    def group_for_algorithm(self, algorithm_name: str) -> str:
        for group_name, algorithms in ALGORITHM_GROUPS.items():
            if algorithm_name in algorithms:
                return group_name
        return "Informed Search"

    def set_solver_algorithm(self, algorithm_name: str) -> None:
        self.algorithm_group_var.set(self.group_for_algorithm(algorithm_name))
        if hasattr(self, "algorithm_combo"):
            self.algorithm_combo.configure(values=self.algorithms_for_current_group())
        self.algorithm_var.set(algorithm_name)
        self.reset_engine()

    def on_algorithm_group_changed(self) -> None:
        algorithms = self.algorithms_for_current_group()
        if hasattr(self, "algorithm_combo"):
            self.algorithm_combo.configure(values=algorithms)
        if self.algorithm_var.get() not in algorithms:
            self.algorithm_var.set(algorithms[0])
        self.reset_engine()

    def build_solver_tab(self) -> None:
        self.build_toolbar(self.solver_tab)
        content = tk.PanedWindow(self.solver_tab, orient="horizontal", sashwidth=5, bg=THEME["bg"], bd=0)
        content.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        left = tk.Frame(content, bg=THEME["panel"], width=360)
        center = tk.Frame(content, bg=THEME["panel"], width=680)
        right = tk.Frame(content, bg=THEME["panel"], width=360)
        content.add(left, minsize=310)
        content.add(center, minsize=470)
        content.add(right, minsize=300)

        tk.Label(left, text="Puzzle Board", bg=THEME["panel"], fg=THEME["text"], font=FONT_PANEL_TITLE).pack(anchor="w", padx=10, pady=(10, 0))
        self.board_view = PuzzleBoardView(left, size=310)
        self.build_manual_input(left)
        self.build_goal_input(left)

        tk.Label(center, text="Search Tree", bg=THEME["panel"], fg=THEME["text"], font=FONT_PANEL_TITLE).pack(anchor="w", padx=10, pady=(10, 0))
        self.tree_view = SearchTreeView(center)

        self.stats_panel = StatsPanel(right)
        self.cost_panel = TextPanel(right, "Current Step Details", height=15)
        self.cost_panel.frame.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = tk.PanedWindow(self.solver_tab, orient="horizontal", sashwidth=5, bg=THEME["bg"], bd=0, height=235)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        self.pseudocode_panel = TextPanel(bottom, "Pseudocode", height=10)
        self.explanation_panel = TextPanel(bottom, "AI Explanation", height=10)
        self.console_panel = TextPanel(bottom, "Console Log", height=10)
        bottom.add(self.pseudocode_panel.frame, minsize=350)
        bottom.add(self.explanation_panel.frame, minsize=420)
        bottom.add(self.console_panel.frame, minsize=350)

    def build_toolbar(self, parent: tk.Widget) -> None:
        toolbar = tk.Frame(parent, bg=THEME["panel"])
        toolbar.pack(fill="x", padx=8, pady=8)
        controls = tk.Frame(toolbar, bg=THEME["panel"])
        controls.pack(fill="x", padx=6, pady=(8, 4))
        actions = tk.Frame(toolbar, bg=THEME["panel"])
        actions.pack(fill="x", padx=6, pady=(4, 8))

        tk.Label(controls, text="Group", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD).pack(side="left", padx=(10, 4))
        group_combo = ttk.Combobox(
            controls,
            textvariable=self.algorithm_group_var,
            values=list(ALGORITHM_GROUPS.keys()),
            width=22,
            state="readonly",
        )
        group_combo.pack(side="left", padx=4)
        group_combo.bind("<<ComboboxSelected>>", lambda _event: self.on_algorithm_group_changed())

        tk.Label(controls, text="Algorithm", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD).pack(side="left", padx=(12, 4))
        self.algorithm_combo = ttk.Combobox(
            controls,
            textvariable=self.algorithm_var,
            values=self.algorithms_for_current_group(),
            width=28,
            state="readonly",
        )
        self.algorithm_combo.pack(side="left", padx=4)
        self.algorithm_combo.bind("<<ComboboxSelected>>", lambda _event: self.reset_engine())

        tk.Label(controls, text="Heuristic", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD).pack(side="left", padx=(12, 4))
        heuristic_combo = ttk.Combobox(
            controls,
            textvariable=self.heuristic_var,
            values=HEURISTICS,
            width=20,
            state="readonly",
        )
        heuristic_combo.pack(side="left", padx=4)
        heuristic_combo.bind("<<ComboboxSelected>>", lambda _event: self.reset_engine())

        tk.Label(controls, text="Goal", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD).pack(side="left", padx=(12, 4))
        goal_combo = ttk.Combobox(
            controls,
            textvariable=self.goal_var,
            values=list(GOAL_STATES.keys()),
            width=10,
            state="readonly",
        )
        goal_combo.pack(side="left", padx=4)
        goal_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_goal_preset())

        tk.Label(controls, text="Speed", bg=THEME["panel"], fg=THEME["text"], font=FONT_BODY_BOLD).pack(side="left", padx=(12, 4))
        tk.Scale(
            controls,
            from_=1,
            to=100,
            orient="horizontal",
            variable=self.speed_var,
            bg=THEME["panel"],
            fg=THEME["text"],
            troughcolor=THEME["panel2"],
            highlightthickness=0,
            font=FONT_BODY,
            length=130,
        ).pack(side="left", padx=4)

        for text, command in [
            ("Reset", self.reset_state),
            ("Shuffle", self.shuffle_state),
            ("Undo", self.undo_step),
            ("Redo", self.redo_step),
            ("Step", self.step_once),
            ("Auto Run", self.auto_run),
            ("Pause", self.pause),
            ("Resume", self.resume),
            ("Stop", self.stop),
            ("Export", self.export_result),
        ]:
            tk.Button(actions, text=text, command=command, **button_style()).pack(side="left", padx=3)

    def build_manual_input(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(
            parent,
            text="Initial State",
            bg=THEME["panel"],
            fg=THEME["text"],
            bd=1,
            relief="solid",
            labelanchor="n",
            font=FONT_BODY_BOLD,
        )
        frame.pack(fill="x", padx=8, pady=8)
        grid_frame = tk.Frame(frame, bg=THEME["panel"])
        grid_frame.pack(padx=8, pady=8)
        self.entries = []
        for index, value in enumerate(self.current_start.tiles):
            entry = tk.Entry(
                grid_frame,
                width=4,
                justify="center",
                bg=THEME["control"],
                fg=THEME["text"],
                insertbackground=THEME["text"],
                relief="solid",
                bd=1,
                font=FONT_GRID,
            )
            entry.insert(0, str(value))
            entry.grid(row=index // BOARD_SIZE, column=index % BOARD_SIZE, padx=3, pady=3)
            self.entries.append(entry)
        tk.Button(frame, text="Apply State", command=self.apply_manual_state, **button_style()).pack(side="left", padx=8, pady=8)
        tk.Button(frame, text="Validate", command=self.validate_state, **button_style()).pack(side="left", padx=8, pady=8)

    def build_goal_input(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(
            parent,
            text="Goal State",
            bg=THEME["panel"],
            fg=THEME["text"],
            bd=1,
            relief="solid",
            labelanchor="n",
            font=FONT_BODY_BOLD,
        )
        frame.pack(fill="x", padx=8, pady=8)
        grid_frame = tk.Frame(frame, bg=THEME["panel"])
        grid_frame.pack(padx=8, pady=8)
        self.goal_entries = []
        for index, value in enumerate(self.current_goal.tiles):
            entry = tk.Entry(
                grid_frame,
                width=4,
                justify="center",
                bg=THEME["control"],
                fg=THEME["text"],
                insertbackground=THEME["text"],
                relief="solid",
                bd=1,
                font=FONT_GRID,
            )
            entry.insert(0, str(value))
            entry.grid(row=index // BOARD_SIZE, column=index % BOARD_SIZE, padx=3, pady=3)
            self.goal_entries.append(entry)
        tk.Button(frame, text="Apply Goal", command=self.apply_manual_goal, **button_style()).pack(side="left", padx=8, pady=8)
        tk.Button(frame, text="Use Preset", command=self.apply_goal_preset, **button_style()).pack(side="left", padx=8, pady=8)

    def read_start_goal(self) -> Tuple[PuzzleState, PuzzleState]:
        values = [entry.get() for entry in self.entries]
        start = PuzzleValidator.parse(values)
        if self.goal_entries:
            goal_values = [entry.get() for entry in self.goal_entries]
            goal = PuzzleValidator.parse(goal_values)
        else:
            goal = self.current_goal
        return start, goal

    def reset_engine(self) -> None:
        try:
            start, goal = self.read_start_goal()
        except ValueError:
            start = self.current_start
            goal = self.current_goal
        self.current_start = start
        self.current_goal = goal
        self.engine.configure(start, goal, self.algorithm_var.get(), self.heuristic_var.get())
        self.running = False
        self.board_view.draw(start)
        self.tree_view.draw(self.engine.algorithm.root if self.engine.algorithm else None, None, [], [], [], [])
        self.pseudocode_panel.set_pseudocode(self.engine.algorithm.pseudocode(), -1)
        self.explanation_panel.set("Press Step or Auto Run to begin.")
        self.cost_panel.set(self.initial_cost_text(start, goal))
        self.stats_panel.update(Metrics())

    def initial_cost_text(self, start: PuzzleState, goal: PuzzleState) -> str:
        lines = [
            f"Initial State: {compact_state(start)}",
            f"Goal State: {compact_state(goal)}",
            f"Valid: {PuzzleValidator.is_valid_tiles(start.tiles)}",
            f"Solvable: {PuzzleValidator.is_solvable(start, goal)}",
        ]
        for heuristic in HEURISTICS:
            lines.append(f"{heuristic}: {HeuristicManager.estimate(start, goal, heuristic):.2f}")
        return "\n".join(lines)

    def apply_manual_state(self) -> None:
        try:
            start, goal = self.read_start_goal()
        except ValueError as exc:
            messagebox.showerror("Invalid State", str(exc))
            return
        self.current_start = start
        self.board_view.draw(start)
        self.reset_engine()
        if not PuzzleValidator.is_solvable(start, goal):
            self.console_panel.append("Warning: this state is not solvable for the selected goal.")

    def apply_manual_goal(self) -> None:
        try:
            start, goal = self.read_start_goal()
        except ValueError as exc:
            messagebox.showerror("Invalid Goal", str(exc))
            return
        self.current_start = start
        self.current_goal = goal
        self.reset_engine()
        if PuzzleValidator.is_solvable(start, goal):
            self.console_panel.append(f"Custom goal applied: {compact_state(goal)}")
        else:
            self.console_panel.append(
                f"Custom goal applied: {compact_state(goal)}. Warning: current start is not solvable for this goal."
            )

    def apply_goal_preset(self) -> None:
        self.pause()
        self.current_goal = PuzzleState(GOAL_STATES[self.goal_var.get()])
        self.set_goal_entries(self.current_goal)
        self.reset_engine()
        self.console_panel.append(f"Goal preset applied: {self.goal_var.get()} = {compact_state(self.current_goal)}")

    def validate_state(self) -> None:
        try:
            start, goal = self.read_start_goal()
        except ValueError as exc:
            messagebox.showerror("Invalid State", str(exc))
            return
        solvable = PuzzleValidator.is_solvable(start, goal)
        messagebox.showinfo(
            "State Validation",
            f"Initial and goal states are valid.\nGoal: {compact_state(goal)}\nSolvable: {solvable}",
        )

    def reset_state(self) -> None:
        self.pause()
        self.current_start = PuzzleState((1, 2, 3, 4, 5, 6, 0, 7, 8))
        self.set_entries(self.current_start)
        self.reset_engine()
        self.console_panel.append("State reset.")

    def shuffle_state(self) -> None:
        self.pause()
        try:
            _, goal = self.read_start_goal()
        except ValueError as exc:
            messagebox.showerror("Invalid Goal", str(exc))
            return
        self.current_start = PuzzleValidator.shuffled_from(goal, moves=36)
        self.set_entries(self.current_start)
        self.reset_engine()
        self.console_panel.append(f"Generated solvable shuffled state: {compact_state(self.current_start)}")

    def set_entries(self, state: PuzzleState) -> None:
        for entry, value in zip(self.entries, state.tiles):
            entry.delete(0, "end")
            entry.insert(0, str(value))

    def set_goal_entries(self, state: PuzzleState) -> None:
        for entry, value in zip(self.goal_entries, state.tiles):
            entry.delete(0, "end")
            entry.insert(0, str(value))

    def ensure_runnable(self) -> bool:
        try:
            start, goal = self.read_start_goal()
        except ValueError as exc:
            messagebox.showerror("Invalid State", str(exc))
            return False
        if (not PuzzleValidator.is_solvable(start, goal)) and self.algorithm_var.get() not in EDUCATIONAL_ALGORITHMS:
            messagebox.showwarning(
                "Unsolvable State",
                "This initial state is not solvable for the selected goal. "
                "Use Shuffle or change the goal state.",
            )
            return False
        if self.engine.config is None or self.engine.config[:2] != (start, goal):
            self.reset_engine()
        return True

    def step_once(self) -> None:
        if not self.ensure_runnable():
            self.pause()
            return
        snapshot = self.engine.step()
        self.update_from_snapshot(snapshot)
        if snapshot.status in {"solved", "failed", "stopped", "local-optimum", "cooled", "stalled", "demo-complete"}:
            self.pause()

    def auto_run(self) -> None:
        if self.running:
            return
        if not self.ensure_runnable():
            return
        self.running = True
        self.console_panel.append("Auto Run started.")
        self.schedule_next_step()

    def schedule_next_step(self) -> None:
        if not self.running:
            return
        self.step_once()
        if self.running:
            delay = max(25, 1050 - self.speed_var.get() * 10)
            self.after_id = self.root.after(delay, self.schedule_next_step)

    def pause(self) -> None:
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def resume(self) -> None:
        if not self.running:
            self.auto_run()

    def stop(self) -> None:
        self.pause()
        if self.engine.algorithm:
            self.engine.algorithm.finished = True
            self.engine.algorithm.status = "stopped"
        self.console_panel.append("Run stopped by user.")

    def undo_step(self) -> None:
        self.pause()
        snapshot = self.engine.undo()
        if snapshot:
            self.update_from_snapshot(snapshot)
            self.console_panel.append(f"Undo to step {snapshot.step_index}.")

    def redo_step(self) -> None:
        snapshot = self.engine.redo()
        if snapshot:
            self.update_from_snapshot(snapshot)
            self.console_panel.append(f"Redo to step {snapshot.step_index}.")

    def update_from_snapshot(self, snapshot: StepSnapshot) -> None:
        node = snapshot.current_node
        state = node.state if node else self.current_start
        highlight = state.blank_index if node and node.moved_tile is not None else None
        self.board_view.draw(state, highlight=highlight)
        root = self.engine.algorithm.root if self.engine.algorithm else None
        self.tree_view.draw(
            root,
            node,
            snapshot.frontier,
            snapshot.explored,
            snapshot.solution_path,
            snapshot.removed_nodes,
        )
        self.stats_panel.update(snapshot.metrics)
        if self.engine.algorithm:
            self.pseudocode_panel.set_pseudocode(
                self.engine.algorithm.pseudocode(),
                snapshot.pseudocode_line,
            )
        self.explanation_panel.set(snapshot.explanation)
        self.cost_panel.set(self.format_step_details(snapshot))
        self.console_panel.append(f"Step {snapshot.step_index}: {snapshot.status} - {snapshot.explanation}")

    def format_step_details(self, snapshot: StepSnapshot) -> str:
        node = snapshot.current_node
        lines = [
            f"Algorithm: {snapshot.algorithm_name}",
            f"Status: {snapshot.status}",
            f"Current Node: {node.describe() if node else '-'}",
            f"Parent: {snapshot.parent_node.describe() if snapshot.parent_node else '-'}",
            f"Depth: {node.depth if node else '-'}",
            f"Cost g(n): {node.cost if node else '-'}",
            f"Heuristic h(n): {node.heuristic if node else '-'}",
            f"f(n)=g(n)+h(n): {(node.cost + node.heuristic) if node else '-'}",
            f"Move: {node.action if node else '-'}",
            f"Action: {snapshot.selected_reason}",
            "",
            "Children:",
        ]
        lines.extend(f"  - {child.describe()} via {child.action}" for child in snapshot.children[:12])
        if not snapshot.children:
            lines.append("  - none")
        lines.append("")
        lines.append("Removed Nodes:")
        lines.extend(f"  - {child.describe()} ({reason})" for child, reason in snapshot.removed_nodes[:12])
        if not snapshot.removed_nodes:
            lines.append("  - none")
        lines.append("")
        lines.append("Open List / Frontier:")
        lines.extend(f"  - {item}" for item in snapshot.open_list[:12])
        if not snapshot.open_list:
            lines.append("  - empty")
        lines.append("")
        lines.append("Closed List / Explored:")
        lines.extend(f"  - {item}" for item in snapshot.closed_list[-12:])
        if not snapshot.closed_list:
            lines.append("  - empty")
        return "\n".join(lines)

    def export_result(self) -> None:
        payload = self.engine.export_payload()
        path = filedialog.asksaveasfilename(
            title="Export Result",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")],
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() == ".csv":
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["step", "algorithm", "status", "current_node", "explanation"],
                )
                writer.writeheader()
                for step in payload["steps"]:
                    writer.writerow(
                        {
                            "step": step["step"],
                            "algorithm": step["algorithm"],
                            "status": step["status"],
                            "current_node": step["current_node"],
                            "explanation": step["explanation"],
                        }
                    )
        else:
            with target.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
        self.console_panel.append(f"Exported result to {target}")

    def run(self) -> None:
        self.root.mainloop()


def run_algorithm_for_compare(
    name: str,
    start: PuzzleState,
    goal: PuzzleState,
    heuristic: str,
    max_steps: int = 6000,
) -> Dict[str, Any]:
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    tracemalloc.reset_peak()
    algorithm = create_algorithm(name, max_expansions=max_steps)
    algorithm.initialize(start, goal, heuristic)
    begin = time.perf_counter()
    steps = 0
    latest: Optional[StepSnapshot] = None
    while not algorithm.finished and steps < max_steps:
        latest = algorithm.next_step()
        steps += 1
    elapsed = time.perf_counter() - begin
    _, peak = tracemalloc.get_traced_memory()
    status = algorithm.status
    if not algorithm.finished and steps >= max_steps:
        status = "limit"
    return {
        "algorithm": name,
        "time": elapsed,
        "memory": peak / 1024,
        "nodes": algorithm.metrics.expanded_nodes,
        "solution_length": algorithm.metrics.solution_length if algorithm.success else "-",
        "status": status,
        "latest": latest,
    }


def run_self_tests() -> None:
    print("Running self-tests...")
    goal = PuzzleState(DEFAULT_GOAL)
    easy = PuzzleState((1, 2, 3, 4, 5, 6, 0, 7, 8))
    assert PuzzleValidator.is_valid_tiles(easy.tiles)
    assert PuzzleValidator.is_solvable(easy, goal)
    assert not PuzzleValidator.is_solvable(PuzzleState((1, 2, 3, 4, 5, 6, 8, 7, 0)), goal)
    assert HeuristicManager.manhattan_distance(easy, goal) == 2
    assert HeuristicManager.misplaced_tiles(easy, goal) == 2
    custom_goal = PuzzleState(GOAL_STATES["Spiral"])
    custom_start = PuzzleValidator.shuffled_from(custom_goal, moves=10)
    assert PuzzleValidator.is_solvable(custom_start, custom_goal)
    assert HeuristicManager.manhattan_distance(custom_goal, custom_goal) == 0

    for algorithm_name in ["Breadth First Search", "Uniform Cost Search", "A*"]:
        record = run_algorithm_for_compare(algorithm_name, easy, goal, "Manhattan Distance", max_steps=100)
        assert record["status"] == "solved", f"{algorithm_name} did not solve easy puzzle"
        assert record["solution_length"] == 2, f"{algorithm_name} expected 2 moves"

    local = run_algorithm_for_compare("Hill Climbing", easy, goal, "Manhattan Distance", max_steps=20)
    assert local["status"] in {"solved", "local-optimum"}

    demo = run_algorithm_for_compare("Minimax", easy, goal, "Manhattan Distance", max_steps=8)
    assert demo["status"] in {"demo-complete", "running"}
    print("All self-tests passed.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AI Search Algorithms Visualization for 8 Puzzle")
    parser.add_argument("--self-test", action="store_true", help="Run core non-GUI tests and exit.")
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_tests()
        return 0
    app = VisualizationApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
