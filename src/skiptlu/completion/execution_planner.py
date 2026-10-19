from __future__ import annotations

from dataclasses import dataclass

from skiptlu.models.activity import Activity
from skiptlu.models.process import DependencyGraph


@dataclass(frozen=True)
class ExecutionPlan:
    ordered_activity_ids: tuple[int, ...]
    cycles: tuple[tuple[int, ...], ...] = ()


class ExecutionPlanner:
    """Create a deterministic dependency-first execution order."""

    def build(self, activities: list[Activity]) -> ExecutionPlan:
        ids = {activity.id for activity in activities}
        graph = self._graph_for(activities)

        # Kahn's algorithm. Keep the original discovery order for stable plans.
        order_index = {activity.id: index for index, activity in enumerate(activities)}
        indegree = {activity_id: 0 for activity_id in ids}
        dependents: dict[int, list[int]] = {activity_id: [] for activity_id in ids}

        for target, prerequisites in graph.dependencies.items():
            if target not in ids:
                continue
            for source in prerequisites:
                if source not in ids or source == target:
                    continue
                indegree[target] += 1
                dependents[source].append(target)

        ready = sorted(
            [activity_id for activity_id, degree in indegree.items() if degree == 0],
            key=order_index.__getitem__,
        )
        ordered: list[int] = []

        while ready:
            current = ready.pop(0)
            ordered.append(current)

            for dependent in sorted(dependents[current], key=order_index.__getitem__):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
                    ready.sort(key=order_index.__getitem__)

        cycles = self._find_cycles(ids, graph, set(ordered))
        return ExecutionPlan(tuple(ordered), tuple(cycles))

    @staticmethod
    def _graph_for(activities: list[Activity]) -> DependencyGraph:
        dependencies: dict[int, list[int]] = {}
        ids = {activity.id for activity in activities}

        for activity in activities:
            sources = [
                restriction.source_activity_id
                for restriction in activity.restrictions
                if restriction.source_activity_id in ids
            ]
            if sources:
                dependencies[activity.id] = list(dict.fromkeys(sources))

        return DependencyGraph(dependencies=dependencies)

    @staticmethod
    def _find_cycles(
        ids: set[int],
        graph: DependencyGraph,
        already_ordered: set[int],
    ) -> list[tuple[int, ...]]:
        remaining = ids - already_ordered
        if not remaining:
            return []

        # A compact deterministic cycle report is sufficient for execution
        # planning; every remaining node belongs to or depends on a cycle.
        cycles: list[tuple[int, ...]] = []
        visited: set[int] = set()
        stack: list[int] = []

        def visit(node: int) -> None:
            if node in stack:
                start = stack.index(node)
                cycles.append(tuple(stack[start:] + [node]))
                return
            if node in visited or node not in remaining:
                return

            visited.add(node)
            stack.append(node)
            for source in graph.prerequisites_for(node):
                if source in remaining:
                    visit(source)
            stack.pop()

        for node in sorted(remaining):
            visit(node)

        # De-duplicate equivalent cycle reports.
        unique: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        for cycle in cycles:
            if cycle not in seen:
                seen.add(cycle)
                unique.append(cycle)
        return unique
