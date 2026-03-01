#!/usr/bin/env bash
# Quality Gates Configuration for B2B Commerce Agent

# ── Enable/disable gates ──────────────────────────────────────────────────────
GATE_FORMAT="false"      # Skip formatting for now
GATE_LINT="false"        # Skip linting for now
GATE_TYPECHECK="false"   # Skip type checking for now
GATE_TESTS="true"        # Run pytest
GATE_COVERAGE="false"    # Skip coverage for now
GATE_SECURITY="false"    # Skip security for now
GATE_PLANKTON="false"    # Custom gate

# ── Coverage threshold ────────────────────────────────────────────────────────
COVERAGE_THRESHOLD=80

# ── Python Commands ───────────────────────────────────────────────────────────
PYTHON_CMD="python3"
PY_TEST_CMD="python3 tests/test_planner.py"

# ── Custom gates (optional) ───────────────────────────────────────────────────
CUSTOM_GATES=()
