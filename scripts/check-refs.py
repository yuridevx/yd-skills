#!/usr/bin/env python3
"""check-refs.py - Deterministic file:line reference validator for test-plan trees.

Two validation modes, both can run in one invocation:

1. file:line REFERENCE VALIDATION (always on)
   Walks every markdown file under <target-dir>, extracts file:line references,
   and verifies each reference points at a real file with a real line in a
   reachable source root. Enforces Rule 2 of linked-testplan's 21-rule checklist.
   SCOPE LIMIT: validates file existence and line-in-range. Does NOT validate
   that the line contains a specific symbol - that is a refinement-pass
   responsibility per Rule 13's `Branch covered` line requiring semantic context.

2. ENTRYPOINT COVERAGE VALIDATION (when --manifest is provided)
   Reads .codex/unit-manifest.json (P1 output) and checks that every entrypoint
   listed there maps to either a per-flow markdown file under <target-dir> OR an
   explicit exclusion record in <target-dir>/../Result.md. Enforces Rule 12 of
   the 21-rule checklist (entrypoint exhaustiveness). Also flags duplicate
   entrypoint-to-flow mappings.

Used by the duo-testplan orchestrator at P5 to catch ref drift mechanically.

Usage:
    python3 scripts/check-refs.py <target-dir>
        [--source-roots <root1> <root2> ...]
        [--manifest <unit-manifest.json>]
        [--result-md <Result.md path for exclusion records>]
        [--json]

Exit codes:
    0  All refs validate AND (if --manifest given) coverage complete.
    1  Some refs failed OR coverage gaps detected.
    2  Argument or IO error.

Output: structured JSON to stdout when --json is set; human-readable otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REF_PATTERNS = [
    # matches "src/foo/Bar.java:42" or "src/foo/Bar.java:42-58"
    re.compile(r"(?P<path>[a-zA-Z0-9_./\\\-]+\.[a-zA-Z0-9]+):(?P<start>\d+)(?:-(?P<end>\d+))?"),
]


@dataclass
class Reference:
    """One file:line reference extracted from a markdown file."""

    source_file: Path
    source_line: int
    target_path: str
    target_start: int
    target_end: int | None


@dataclass
class Failure:
    """One validation failure."""

    ref: Reference | None
    kind: str  # ref kinds + coverage kinds
    detail: str

    def to_dict(self) -> dict:
        return {
            "source_file": str(self.ref.source_file) if self.ref else None,
            "source_line": self.ref.source_line if self.ref else None,
            "target_path": self.ref.target_path if self.ref else None,
            "target_start": self.ref.target_start if self.ref else None,
            "target_end": self.ref.target_end if self.ref else None,
            "kind": self.kind,
            "detail": self.detail,
        }


@dataclass
class Result:
    """Aggregate validation result."""

    total_refs: int = 0
    total_entrypoints: int = 0
    failures: list[Failure] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def extract_refs(md_path: Path) -> Iterable[Reference]:
    """Yield every file:line reference in a markdown file."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"warning: cannot read {md_path}: {exc}", file=sys.stderr)
        return

    for lineno, line in enumerate(text.splitlines(), start=1):
        # Skip lines inside fenced code blocks for ref extraction? No - flow pages
        # use file:line refs in bullets, not code blocks. But we do skip lines
        # inside backticks for command examples.
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        for pattern in REF_PATTERNS:
            for match in pattern.finditer(line):
                target = match.group("path")
                # Filter out things that aren't really refs: URLs, version strings, etc.
                if target.startswith(("http://", "https://", "ftp://", "://")):
                    continue
                if not _looks_like_source_path(target):
                    continue
                start = int(match.group("start"))
                end_raw = match.group("end")
                end = int(end_raw) if end_raw else None
                yield Reference(md_path, lineno, target, start, end)


def _looks_like_source_path(s: str) -> bool:
    """True if `s` looks like a source-code path (not a version or random match)."""
    if "/" not in s and "\\" not in s:
        # Single-segment refs like "Foo.java:42" are valid but only if extension is source-like.
        return _looks_like_source_extension(s)
    return _looks_like_source_extension(s)


def _looks_like_source_extension(s: str) -> bool:
    """True if path ends in a recognized source extension."""
    suffixes = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
        ".java", ".kt", ".kts", ".scala", ".groovy",
        ".go", ".rs", ".c", ".cpp", ".cc", ".h", ".hpp",
        ".cs", ".vb", ".fs",
        ".rb", ".php", ".swift", ".m", ".mm",
        ".sh", ".bash", ".zsh", ".ps1",
        ".sql",
        ".yaml", ".yml", ".toml", ".json", ".xml", ".proto",
        ".gradle", ".sbt",
    }
    return any(s.lower().endswith(suffix) for suffix in suffixes)


def resolve_target(ref: Reference, source_roots: list[Path]) -> Path | None:
    """Find the actual file for a reference under one of the source roots.

    Returns the first matching path or None. Tries:
    1. ref.target_path as-is from each source root.
    2. ref.target_path treated as already-absolute.
    """
    candidate = Path(ref.target_path)
    if candidate.is_absolute() and candidate.is_file():
        return candidate
    for root in source_roots:
        candidate = root / ref.target_path
        if candidate.is_file():
            return candidate
    return None


def count_lines(path: Path) -> int:
    """Return the number of lines in a file. Returns 0 on read failure."""
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def validate_ref(ref: Reference, source_roots: list[Path]) -> Failure | None:
    """Return a Failure if the ref is bad, else None."""
    target = resolve_target(ref, source_roots)
    if target is None:
        return Failure(
            ref=ref,
            kind="no-such-file",
            detail=f"target file not found under any source root: {ref.target_path}",
        )
    line_count = count_lines(target)
    if ref.target_start < 1 or ref.target_start > line_count:
        return Failure(
            ref=ref,
            kind="line-out-of-range",
            detail=f"line {ref.target_start} out of range (file has {line_count} lines)",
        )
    if ref.target_end is not None and ref.target_end > line_count:
        return Failure(
            ref=ref,
            kind="line-out-of-range",
            detail=f"end line {ref.target_end} out of range (file has {line_count} lines)",
        )
    return None


def validate_tree(target_dir: Path, source_roots: list[Path]) -> Result:
    """Walk every markdown file under target_dir and validate refs."""
    result = Result()
    for md in sorted(target_dir.rglob("*.md")):
        for ref in extract_refs(md):
            result.total_refs += 1
            failure = validate_ref(ref, source_roots)
            if failure is not None:
                result.failures.append(failure)
    return result


def collect_flow_ids_from_tree(target_dir: Path) -> set[str]:
    """Find every flow-id present in the target tree.

    A flow-id is the basename (without .md) of every markdown file under
    target_dir/<repo>/<svc>/flows/ and target_dir/cross-app/flows/.
    """
    flow_ids: set[str] = set()
    for md in target_dir.rglob("flows/*.md"):
        flow_ids.add(md.stem)
    return flow_ids


def collect_exclusions_from_result_md(result_md_path: Path) -> set[str]:
    """Parse exclusion entries from a Result.md ## Exclusions section.

    Looks for lines under a '## Exclusions' heading of the form `- <file>:<line> - ...`
    and collects the entrypoint coordinates as `<file>:<line>` strings.
    """
    exclusions: set[str] = set()
    if not result_md_path.is_file():
        return exclusions
    try:
        text = result_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return exclusions

    in_exclusions = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_exclusions = stripped.lower().startswith("## exclusion")
            continue
        if not in_exclusions:
            continue
        if not stripped.startswith("- "):
            continue
        for pattern in REF_PATTERNS:
            for match in pattern.finditer(stripped):
                target = match.group("path")
                if _looks_like_source_path(target):
                    exclusions.add(f"{target}:{match.group('start')}")
                    break
    return exclusions


def validate_manifest_coverage(
    manifest_path: Path,
    target_dir: Path,
    result_md_path: Path | None,
) -> tuple[int, list[Failure]]:
    """Check entrypoint exhaustiveness against the manifest.

    Returns (total_entrypoints, failures).
    """
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return 0, [Failure(ref=None, kind="manifest-invalid", detail=f"{manifest_path}: {exc}")]

    tree_flow_ids = collect_flow_ids_from_tree(target_dir)
    exclusion_coords = (
        collect_exclusions_from_result_md(result_md_path) if result_md_path else set()
    )

    failures: list[Failure] = []
    total = 0
    flow_id_to_entry: dict[str, str] = {}  # flow_id → "<file>:<line>" for duplicate detection

    repos = manifest.get("repos", {})
    for repo_name, repo_data in repos.items():
        units: dict[str, dict] = {}
        units.update(repo_data.get("services", {}))
        if "_common" in repo_data:
            units["_common"] = repo_data["_common"]
        for unit_id, unit_data in units.items():
            for entry in unit_data.get("entrypoints", []) or []:
                total += 1
                flow_id = entry.get("flow_id")
                entry_coord = f"{entry.get('entry_file')}:{entry.get('entry_line')}"
                if not flow_id:
                    failures.append(
                        Failure(
                            ref=None,
                            kind="manifest-missing-flow-id",
                            detail=f"{repo_name}/{unit_id} entrypoint at {entry_coord} has no flow_id",
                        )
                    )
                    continue
                if flow_id in flow_id_to_entry and flow_id_to_entry[flow_id] != entry_coord:
                    failures.append(
                        Failure(
                            ref=None,
                            kind="duplicate-flow-id",
                            detail=(
                                f"flow_id '{flow_id}' assigned to two entrypoints: "
                                f"{flow_id_to_entry[flow_id]} and {entry_coord}"
                            ),
                        )
                    )
                flow_id_to_entry[flow_id] = entry_coord
                if flow_id in tree_flow_ids:
                    continue
                if entry_coord in exclusion_coords:
                    continue
                failures.append(
                    Failure(
                        ref=None,
                        kind="orphan-entrypoint",
                        detail=(
                            f"entrypoint {entry_coord} (flow_id={flow_id}) in {repo_name}/{unit_id} "
                            f"has no corresponding flow file in {target_dir} and no exclusion in Result.md"
                        ),
                    )
                )
    return total, failures


def print_human(result: Result, target_dir: Path) -> None:
    if result.passed:
        msg = f"OK: {result.total_refs} refs validated under {target_dir}"
        if result.total_entrypoints:
            msg += f"; {result.total_entrypoints} entrypoints covered"
        print(msg)
        return
    summary = (
        f"FAIL: {len(result.failures)} issues "
        f"({result.total_refs} refs, {result.total_entrypoints} entrypoints checked) under {target_dir}"
    )
    print(summary, file=sys.stderr)
    print("", file=sys.stderr)
    for failure in result.failures:
        if failure.ref is not None:
            print(
                f"  {failure.ref.source_file}:{failure.ref.source_line}  "
                f"-> {failure.ref.target_path}:{failure.ref.target_start}  "
                f"[{failure.kind}] {failure.detail}",
                file=sys.stderr,
            )
        else:
            print(f"  [{failure.kind}] {failure.detail}", file=sys.stderr)


def print_json(result: Result, target_dir: Path) -> None:
    payload = {
        "target_dir": str(target_dir),
        "total_refs": result.total_refs,
        "total_entrypoints": result.total_entrypoints,
        "passed": result.passed,
        "failure_count": len(result.failures),
        "failures": [f.to_dict() for f in result.failures],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory containing markdown files to validate (e.g. Duo/TestPlan-<slug>/test-plan/).",
    )
    parser.add_argument(
        "--source-roots",
        nargs="+",
        type=Path,
        default=[Path.cwd()],
        help="Source-code root directories to resolve refs against (default: cwd).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to .codex/unit-manifest.json. Enables entrypoint coverage validation (Rule 12).",
    )
    parser.add_argument(
        "--result-md",
        type=Path,
        default=None,
        help="Path to Result.md for parsing the ## Exclusions section (used with --manifest).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON on stdout instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    if not args.target_dir.is_dir():
        print(f"error: not a directory: {args.target_dir}", file=sys.stderr)
        return 2

    for root in args.source_roots:
        if not root.is_dir():
            print(f"error: source root not a directory: {root}", file=sys.stderr)
            return 2

    if args.manifest is not None and not args.manifest.is_file():
        print(f"error: manifest not a file: {args.manifest}", file=sys.stderr)
        return 2

    result = validate_tree(args.target_dir, args.source_roots)

    if args.manifest is not None:
        result_md = args.result_md
        if result_md is None:
            candidate = args.target_dir.parent / "Result.md"
            if candidate.is_file():
                result_md = candidate
        total, manifest_failures = validate_manifest_coverage(
            args.manifest, args.target_dir, result_md
        )
        result.total_entrypoints = total
        result.failures.extend(manifest_failures)

    if args.json:
        print_json(result, args.target_dir)
    else:
        print_human(result, args.target_dir)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
