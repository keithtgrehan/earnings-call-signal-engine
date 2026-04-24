"""Import-safe adapter placeholders for optional roadmap components.

These modules intentionally avoid loading models or heavy runtimes at import time.
They only expose availability checks and clear install hints for future benchmark
and enrichment workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import Iterable


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
    return [
        dependency
        for dependency in dependencies
        if not module_available(dependency.module_name)
    ]


def _normalize_optional_groups(
    optional_groups: str | Iterable[str],
) -> tuple[str, ...]:
    if isinstance(optional_groups, str):
        return tuple(
            group.strip() for group in optional_groups.split(",") if group.strip()
        )
    return tuple(group for group in optional_groups if group)


def require_dependencies(
    *,
    adapter_name: str,
    optional_groups: str | Iterable[str],
    dependencies: tuple[AdapterDependency, ...],
    purpose: str,
) -> None:
    missing = missing_dependencies(dependencies)
    if not missing:
        return

    normalized_groups = _normalize_optional_groups(optional_groups)
    missing_modules = ", ".join(
        sorted(dependency.module_name for dependency in missing)
    )
    missing_packages = ", ".join(
        sorted(dependency.package_name for dependency in missing)
    )
    group_label = "group" if len(normalized_groups) == 1 else "groups"
    group_text = ", ".join(normalized_groups)
    install_groups = ",".join(normalized_groups)
    raise ImportError(
        f"{adapter_name} requires optional dependency {group_label} "
        f"'{group_text}' for {purpose}. Missing modules: {missing_modules}. "
        f"Missing packages: {missing_packages}. Install with "
        f"`pip install .[{install_groups}]`."
    )


__all__ = [
    "AdapterDependency",
    "missing_dependencies",
    "module_available",
    "require_dependencies",
]
