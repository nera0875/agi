#!/bin/bash
# Parallel MCP Installation Orchestrator
# Demonstrates optimal pattern: Launch → Work → Poll → Synthesize

set -e

echo "=========================================="
echo "PARALLEL MCP INSTALLATION ORCHESTRATOR"
echo "=========================================="

# Configuration
WORK_DIR="/home/pilote/projet/agi"
OUTPUT_DIR="/tmp/mcp_parallel"
mkdir -p "$OUTPUT_DIR"

# MCPs to install (add real configs here)
declare -A MCP_CONFIGS
MCP_CONFIGS["test-stdio"]='{"command":"echo","args":["test"]}'
MCP_CONFIGS["test-python"]='{"command":"python3","args":["-c","print(\"hello\")"]}'

echo ""
echo "[1] Launching background installations..."
echo ""

# Launch each MCP installation in background
PIDS=()
for mcp_name in "${!MCP_CONFIGS[@]}"; do
    config="${MCP_CONFIGS[$mcp_name]}"
    log_file="$OUTPUT_DIR/install_$mcp_name.log"

    # Launch Claude headless in background
    (
        cd "$WORK_DIR"
        python3 cortex/workers/install_mcp.py "$mcp_name" "$config" \
            > "$log_file" 2>&1
        echo $? > "$OUTPUT_DIR/${mcp_name}_exit.code"
    ) &

    pid=$!
    PIDS+=($pid)
    echo "  ✓ Launched: $mcp_name (PID: $pid)"
done

echo ""
echo "[2] Working while installations run..."
echo "  - Analyzing codebase structure"
echo "  - Updating documentation"
echo "  - Preparing synthesis report"
sleep 2

echo ""
echo "[3] Polling results..."
echo ""

# Wait for all background tasks
for pid in "${PIDS[@]}"; do
    wait $pid 2>/dev/null || true
done

# Collect results
SUCCESS_COUNT=0
FAILED_COUNT=0

for mcp_name in "${!MCP_CONFIGS[@]}"; do
    result_file="$OUTPUT_DIR/mcp_install_$mcp_name.json"

    if [ -f "$result_file" ]; then
        status=$(jq -r '.status' "$result_file" 2>/dev/null || echo "unknown")
        tools_count=$(jq -r '.tools | length' "$result_file" 2>/dev/null || echo "0")

        if [ "$status" = "success" ]; then
            echo "  ✓ $mcp_name: SUCCESS ($tools_count tools)"
            ((SUCCESS_COUNT++))
        else
            error=$(jq -r '.errors[0]' "$result_file" 2>/dev/null || echo "Unknown error")
            echo "  ✗ $mcp_name: FAILED - $error"
            ((FAILED_COUNT++))
        fi
    else
        echo "  ✗ $mcp_name: NO RESULT FILE"
        ((FAILED_COUNT++))
    fi
done

echo ""
echo "[4] Synthesis:"
echo "  Total MCPs: ${#MCP_CONFIGS[@]}"
echo "  Success: $SUCCESS_COUNT"
echo "  Failed: $FAILED_COUNT"
echo ""
echo "=========================================="
echo "PATTERN: Launch → Work → Poll → Synthesize"
echo "BENEFIT: Zero blocking, maximum efficiency"
echo "=========================================="

# Cleanup old results
echo ""
echo "Results saved in: $OUTPUT_DIR"
