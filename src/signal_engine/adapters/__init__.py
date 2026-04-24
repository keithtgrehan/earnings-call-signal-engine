"""Import-safe adapter placeholders for optional roadmap components.

These modules intentionally avoid loading models or heavy runtimes at import time.
They only expose availability checks and clear install hints for future benchmark
and enrichment workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True)
class AdapterDependency:
    module_name: str
    package_name: str


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def missing_dependencies(
    dependencies: tuple[AdapterDependency, ...],
) -> list[AdapterDependency]:
    return [dependency for dependency in dependencies if not module_available(dependency.module_name)]


def require_dependencies(
    *,
    adapter_name: str,
    optional_group: str,
    dependencies: tuple[AdapterDependency, ...],
    purpose: str,
) -> None:
    missing = missing_dependencies(dependencies)
    if not missing:
        return
    missing_modules = ", ".join(sorted(dependency.module_name for dependency in missing))
    raise ImportError(
        f"{adapter_name} requires optional dependency group '{optional_group}' for {purpose}. "
        f"Missing modules: {missing_modules}. Install with `pip install .[{optional_group}]`."
    )


__all__ = [
    "AdapterDependency",
    "missing_dependencies",
    "module_available",
    "require_dependencies",
]
