"""Runtime and static custody guards for scientific execution."""

from __future__ import annotations

import ast
import functools
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass
class TraceSink:
    label: str
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, operation: str, **metadata: Any) -> None:
        self.events.append({"operation": operation, **metadata})


_ACTIVE_SINK: ContextVar[TraceSink | None] = ContextVar(
    "v3_active_serializing_trace_sink", default=None
)


@contextmanager
def serializing_trace_context(label: str) -> Iterator[TraceSink]:
    if _ACTIVE_SINK.get() is not None:
        raise RuntimeError("nested serializing trace contexts are forbidden")
    sink = TraceSink(str(label))
    token = _ACTIVE_SINK.set(sink)
    try:
        yield sink
    finally:
        _ACTIVE_SINK.reset(token)


def require_trace_sink(operation: str, **metadata: Any) -> TraceSink:
    sink = _ACTIVE_SINK.get()
    if sink is None:
        raise RuntimeError(
            f"{operation} requires an active serializing trace context"
        )
    sink.record(operation, **metadata)
    return sink


def traced_execution(function):
    """Run one helper inside a sink and attach its event ledger to dict output."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        with serializing_trace_context(function.__qualname__) as sink:
            result = function(*args, **kwargs)
            if isinstance(result, dict):
                result["_runtime_trace_events"] = tuple(sink.events)
            return result

    return wrapper


def audit_runner_trace_contexts(scripts_root: Path) -> tuple[str, ...]:
    """Find V3.2 public generation/scoring calls outside a trace context."""

    violations: list[str] = []
    for path in sorted(scripts_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "v32"
                and function.attr in {"generate_world", "score_world"}
            ):
                continue
            enclosing: ast.AST | None = node
            guarded = False
            while enclosing is not None and not isinstance(
                enclosing, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                enclosing = parents.get(enclosing)
            if isinstance(enclosing, (ast.FunctionDef, ast.AsyncFunctionDef)):
                intentional_refusal_probe = (
                    enclosing.name == "run_trace_guard_audit"
                    and function.attr == "generate_world"
                )
                decorated = any(
                    (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "traced_execution"
                    )
                    or (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "traced_execution"
                    )
                    for decorator in enclosing.decorator_list
                )
                guarded = intentional_refusal_probe or any(
                    isinstance(child, (ast.With, ast.AsyncWith))
                    and any(
                        (
                            isinstance(item.context_expr, ast.Call)
                            and (
                                (
                                    isinstance(
                                        item.context_expr.func, ast.Name
                                    )
                                    and item.context_expr.func.id
                                    == "serializing_trace_context"
                                )
                                or (
                                    isinstance(
                                        item.context_expr.func, ast.Attribute
                                    )
                                    and item.context_expr.func.attr
                                    == "serializing_trace_context"
                                )
                            )
                        )
                        for item in child.items
                    )
                    for child in ast.walk(enclosing)
                ) or decorated
            if not guarded:
                violations.append(
                    f"{path.name}:{node.lineno}: unguarded v32.{function.attr}"
                )
    return tuple(violations)
