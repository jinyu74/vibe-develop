#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROFILES_FILE="$SCRIPT_DIR/workspace-profiles.yaml"

usage() {
  cat <<USAGE
Usage: $0 <service-name> [branch-name]

Sets up a Git sparse checkout filtered to the specified service profile,
so only relevant files are visible on disk and to the AI assistant.

Arguments:
  service-name   One of: file-watcher, file-relay, analysis-api,
                 analysis-web, monitor-api, monitor-web
  branch-name    Optional. If provided, creates and checks out a new
                 branch (e.g., feature/FW-v0.0.1)

Examples:
  $0 file-watcher feature/FW-v0.0.1
  $0 analysis-api
USAGE
  exit 1
}

VALID_SERVICES=(file-watcher file-relay analysis-api analysis-web monitor-api monitor-web)

validate_service() {
  local service="$1"
  for valid in "${VALID_SERVICES[@]}"; do
    if [[ "$service" == "$valid" ]]; then
      return 0
    fi
  done
  echo "Error: Unknown service '$service'"
  echo "Valid services: ${VALID_SERVICES[*]}"
  exit 1
}

parse_profile() {
  local service="$1"
  local in_common=false
  local in_service=false
  local common_paths=()
  local service_paths=()

  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// /}" ]] && continue

    if [[ "$line" =~ ^_common: ]]; then
      in_common=true
      in_service=false
      continue
    fi

    if [[ "$line" =~ ^${service}: ]]; then
      in_service=true
      in_common=false
      continue
    fi

    if [[ "$line" =~ ^[a-z_] && ! "$line" =~ ^[[:space:]] ]]; then
      in_common=false
      in_service=false
      continue
    fi

    local trimmed
    trimmed="$(echo "$line" | sed 's/^[[:space:]]*-[[:space:]]*//' | sed 's/[[:space:]]*$//')"

    if [[ "$trimmed" == "include:" ]]; then
      continue
    fi

    if [[ "$trimmed" == "*common" ]]; then
      service_paths+=("${common_paths[@]}")
      continue
    fi

    if $in_common; then
      common_paths+=("$trimmed")
    elif $in_service; then
      service_paths+=("$trimmed")
    fi
  done < "$PROFILES_FILE"

  printf '%s\n' "${service_paths[@]}"
}

main() {
  [[ $# -lt 1 ]] && usage

  local service="$1"
  local branch="${2:-}"

  validate_service "$service"

  if ! command -v git &>/dev/null; then
    echo "Error: git is not installed"
    exit 1
  fi

  cd "$REPO_ROOT"

  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: Working tree has uncommitted changes. Commit or stash first."
    exit 1
  fi

  if [[ -n "$branch" ]]; then
    echo "Creating branch: $branch"
    git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
  fi

  echo "Enabling sparse checkout for service: $service"
  git sparse-checkout init --cone 2>/dev/null || true
  git sparse-checkout set --no-cone $(parse_profile "$service" | tr '\n' ' ')

  echo ""
  echo "Sparse checkout configured for '$service'."
  echo "Visible paths:"
  git sparse-checkout list 2>/dev/null | head -30
  echo ""
  echo "To restore full checkout later:"
  echo "  git sparse-checkout disable"
}

main "$@"
