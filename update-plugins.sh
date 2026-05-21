#!/usr/bin/env bash
# Update all installed Claude Code plugins.
#
# Refreshes every configured marketplace, then runs `claude plugin update` for
# each installed plugin in its own scope. Emits a per-plugin status line and a
# summary at the end. Exit code is nonzero if any plugin update failed.

set -o pipefail

if ! command -v claude >/dev/null 2>&1; then
    echo "claude CLI not found on PATH." >&2
    exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
    echo "jq not found on PATH. Install with 'brew install jq' (macOS) or 'apt install jq' (Debian/Ubuntu)." >&2
    exit 1
fi

echo "Refreshing marketplaces..."
claude plugin marketplace update
if [ $? -ne 0 ]; then
    echo "  Marketplace refresh exited nonzero - continuing."
fi

echo
echo "Enumerating installed plugins..."
json=$(claude plugin list --json)
if [ $? -ne 0 ] || [ -z "$json" ]; then
    echo "Failed to list plugins." >&2
    exit 1
fi

count=$(echo "$json" | jq 'length')
if [ "$count" = "0" ]; then
    echo "No plugins installed."
    exit 0
fi

updated=()
current=()
failed=()

while IFS=$'\t' read -r id scope version; do
    echo
    echo "-> $id [scope=$scope, version=$version]"
    output=$(claude plugin update "$id" --scope "$scope" 2>&1)
    exit_code=$?
    echo "$output"

    if [ $exit_code -ne 0 ]; then
        failed+=("$id")
    elif echo "$output" | grep -q 'updated from'; then
        updated+=("$id")
    elif echo "$output" | grep -q 'already at the latest'; then
        current+=("$id")
    else
        # Unrecognized success output - surface it as failed so it gets noticed.
        failed+=("$id")
    fi
done < <(echo "$json" | jq -r '.[] | [.id, .scope, .version] | @tsv')

echo
echo "===== Summary ====="
echo "Updated:        ${#updated[@]}"
if [ ${#updated[@]} -gt 0 ]; then
    for id in "${updated[@]}"; do echo "  - $id"; done
fi
echo "Already latest: ${#current[@]}"
echo "Failed:         ${#failed[@]}"
if [ ${#failed[@]} -gt 0 ]; then
    for id in "${failed[@]}"; do echo "  - $id"; done
fi

if [ ${#updated[@]} -gt 0 ]; then
    echo
    echo "Restart Claude Code to apply updates."
fi

if [ ${#failed[@]} -gt 0 ]; then exit 1; else exit 0; fi
