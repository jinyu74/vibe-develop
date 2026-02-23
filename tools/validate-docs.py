#!/usr/bin/env python3
"""
Document cross-reference validator for vibe-develop project.

Validates:
  1. Required documents exist (01, 02, 03, 05, 08, 09) + CONTEXT.md
  2. F-IDs in 01-requirements.md are referenced in 05-api-spec.md and 09-test-cases.md
  3. S-IDs in 02-screen-spec.md reference valid F-IDs
  4. TC-IDs in 09-test-cases.md follow TC-{F-ID}-xx pattern
  5. 03-api-contract.md state is one of Draft/Review/Locked
  6. overview.md lists all services with correct version

Usage:
  python tools/validate-docs.py                    # validate all services
  python tools/validate-docs.py --service auth-api  # validate one service
"""

import re
import sys
from pathlib import Path

DOCS_DIR = Path("docs")
REQUIRED_DOCS = [
    "01-requirements.md",
    "02-screen-spec.md",
    "03-api-contract.md",
    "05-api-spec.md",
    "08-implementation-guide.md",
    "09-test-cases.md",
]

F_ID_PATTERN = re.compile(r"\bF\d{3}\b")
S_ID_PATTERN = re.compile(r"\bS\d{3}\b")
TC_ID_PATTERN = re.compile(r"\bTC-F\d{3}-\d{2}\b")
CONTRACT_STATE_PATTERN = re.compile(r"\*\*상태\*\*:\s*`(Draft|Review|Locked)`")


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def find_services() -> list[tuple[str, str]]:
    """Return list of (service_name, version) tuples."""
    services = []
    for context in DOCS_DIR.glob("*/CONTEXT.md"):
        svc = context.parent.name
        if svc.startswith("_"):
            continue
        for version_dir in sorted(context.parent.iterdir()):
            if version_dir.is_dir() and not version_dir.name.startswith("_"):
                services.append((svc, version_dir.name))
    return services


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_ids(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def validate_service(svc: str, version: str, result: ValidationResult) -> None:
    base = DOCS_DIR / svc / version
    prefix = f"[{svc}/{version}]"

    # 1. Check required documents
    for doc in REQUIRED_DOCS:
        if not (base / doc).exists():
            result.error(f"{prefix} Missing required document: {doc}")

    # Check CONTEXT.md
    context_path = DOCS_DIR / svc / "CONTEXT.md"
    if not context_path.exists():
        result.error(f"[{svc}] Missing CONTEXT.md")

    # 2. Extract F-IDs from requirements
    req_text = read_file(base / "01-requirements.md")
    f_ids = extract_ids(req_text, F_ID_PATTERN)
    if not f_ids and req_text:
        result.warn(f"{prefix} No F-IDs found in 01-requirements.md")

    # 3. Check F-IDs referenced in api-spec
    api_text = read_file(base / "05-api-spec.md")
    api_f_ids = extract_ids(api_text, F_ID_PATTERN)
    for fid in f_ids:
        if fid not in api_f_ids and api_text:
            result.warn(f"{prefix} {fid} in requirements but not referenced in 05-api-spec.md")

    # 4. Check F-IDs referenced in test-cases
    tc_text = read_file(base / "09-test-cases.md")
    tc_f_ids = extract_ids(tc_text, F_ID_PATTERN)
    tc_ids = extract_ids(tc_text, TC_ID_PATTERN)
    for fid in f_ids:
        if fid not in tc_f_ids and tc_text:
            result.warn(f"{prefix} {fid} in requirements but no test case in 09-test-cases.md")

    # 5. Validate TC-ID format
    for tc_id in tc_ids:
        parts = tc_id.split("-")
        ref_fid = parts[1]  # TC-F001-01 -> F001
        if ref_fid not in f_ids and f_ids:
            result.error(f"{prefix} {tc_id} references {ref_fid} which is not in 01-requirements.md")

    # 6. Check S-IDs reference valid F-IDs
    screen_text = read_file(base / "02-screen-spec.md")
    s_ids = extract_ids(screen_text, S_ID_PATTERN)
    screen_f_ids = extract_ids(screen_text, F_ID_PATTERN)
    for fid in screen_f_ids:
        if fid not in f_ids and f_ids:
            result.warn(f"{prefix} {fid} in 02-screen-spec.md but not in 01-requirements.md")

    # 7. Validate api-contract state
    contract_text = read_file(base / "03-api-contract.md")
    if contract_text:
        state_match = CONTRACT_STATE_PATTERN.search(contract_text)
        if not state_match:
            result.warn(f"{prefix} 03-api-contract.md does not declare a state (Draft/Review/Locked)")
        else:
            state = state_match.group(1)
            if state not in ("Draft", "Review", "Locked"):
                result.error(f"{prefix} 03-api-contract.md has invalid state: {state}")

    # 8. Cross-check api-contract types with api-spec
    if contract_text and api_text:
        contract_endpoints = set(re.findall(r"(?:GET|POST|PUT|PATCH|DELETE)\s+(/\S+)", contract_text))
        api_endpoints = set(re.findall(r"(?:GET|POST|PUT|PATCH|DELETE)\s+(/\S+)", api_text))
        for ep in contract_endpoints:
            if ep not in api_endpoints and api_endpoints:
                result.warn(
                    f"{prefix} Endpoint {ep} in 03-api-contract.md but not in 05-api-spec.md"
                )


def validate_overview(services: list[tuple[str, str]], result: ValidationResult) -> None:
    overview = read_file(DOCS_DIR / "overview.md")
    if not overview:
        result.error("[global] docs/overview.md not found")
        return
    for svc, _version in services:
        if svc not in overview:
            result.error(f"[global] Service '{svc}' not listed in docs/overview.md")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate document cross-references")
    parser.add_argument("--service", "-s", help="Validate only this service")
    args = parser.parse_args()

    result = ValidationResult()
    services = find_services()

    if args.service:
        services = [(s, v) for s, v in services if s == args.service]
        if not services:
            print(f"Service '{args.service}' not found in docs/")
            return 1

    if not services:
        print("No services found in docs/ (this is OK if no services are set up yet)")
        return 0

    for svc, version in services:
        validate_service(svc, version, result)

    validate_overview(services, result)

    # Report
    if result.errors:
        print(f"\n{'='*60}")
        print(f"  ERRORS: {len(result.errors)}")
        print(f"{'='*60}")
        for e in result.errors:
            print(f"  ✗ {e}")

    if result.warnings:
        print(f"\n{'='*60}")
        print(f"  WARNINGS: {len(result.warnings)}")
        print(f"{'='*60}")
        for w in result.warnings:
            print(f"  ⚠ {w}")

    if result.ok and not result.warnings:
        print("✓ All document validations passed.")

    if result.ok:
        print(f"\nResult: PASS ({len(result.warnings)} warnings)")
        return 0
    else:
        print(f"\nResult: FAIL ({len(result.errors)} errors, {len(result.warnings)} warnings)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
