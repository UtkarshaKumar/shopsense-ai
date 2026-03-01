# Multi-Agent SWE Workflow

A fully-automated software engineering loop that pairs a **Builder** agent with a **Reviewer** agent across isolated git worktrees, with structured quality gates, stacked PR support, and multiple review cycles.

---

## Overview

```
SETUP
──────────────────────────────────────────────────────
 Feature spec (.md)  →  Worktree  →  Builder + Reviewer
                         (safe        (study codebase
                          copy)        in parallel)

THE LOOP  (up to N cycles, fully automatic)
──────────────────────────────────────────────────────
                ┌─ INNER LOOP (up to N retries) ──┐
                │                                  │
 1. BUILD  ──►  2. VERIFY  ──fail──►  2b. FIX ───►┘
 (TDD)          (quality gates)       (targeted)
                    │
                   pass
                    │
 3. PUBLISH  ──►  4. REVIEW
 (commit,         (Reviewer reads
  push, PR)        diff only)
                    │           │
                  PASS        FAIL
                    │           │
                  DONE      findings ──► next cycle
                  (PR ready   (structured, typed,
                  for human)   file:line format)
```

---

## Quick Start

### 1. Install dependencies

```bash
# Required
brew install git              # or apt install git
npm install -g @anthropic-ai/claude-code   # claude CLI

# Recommended
brew install gh               # GitHub CLI for PR management
brew install jq               # JSON processing for coverage gates
brew install tree             # Better directory trees in context
```

### 2. Bootstrap a project

```bash
# Copy the workflow into your project
cp -r "path/to/Multi-Agent SWE Workflow" your-project/workflow/
chmod +x your-project/workflow/orchestrate.sh
chmod +x your-project/workflow/quality-gates/run-gates.sh
chmod +x your-project/workflow/quality-gates/gates/*.sh
chmod +x your-project/workflow/stacked-pr/stacked-pr.sh
chmod +x your-project/workflow/context/generate-context.sh

# Configure quality gates
cp workflow/quality-gates/gates.config.example.sh \
   workflow/quality-gates/gates.config.sh
# → Edit gates.config.sh for your stack
```

### 3. Write a spec

```bash
cp workflow/spec-template.md specs/my-feature.md
# → Fill in the spec following the template
```

### 4. Run the workflow

```bash
# Single-branch feature
./workflow/orchestrate.sh specs/my-feature.md

# Stacked PRs (large feature split into layers)
./workflow/orchestrate.sh specs/my-feature.md --stack

# Dry run (validate spec + gates, no commits)
./workflow/orchestrate.sh specs/my-feature.md --dry-run

# More cycles, more retries
./workflow/orchestrate.sh specs/my-feature.md --max-cycles 5 --max-retries 8
```

---

## File Reference

```
workflow/
├── WORKFLOW.md                 ← this file
├── orchestrate.sh              ← main entry point
├── spec-template.md            ← copy & fill for each feature
│
├── agents/
│   ├── builder.md              ← Builder system prompt
│   └── reviewer.md             ← Reviewer system prompt
│
├── quality-gates/
│   ├── run-gates.sh            ← gate runner (called by orchestrator)
│   ├── gates.config.example.sh ← copy → gates.config.sh
│   └── gates/
│       ├── format.sh           ← prettier / black / gofmt
│       ├── lint.sh             ← eslint / pylint / golangci-lint
│       ├── typecheck.sh        ← tsc / mypy / go build
│       ├── tests.sh            ← jest / pytest / go test
│       ├── coverage.sh         ← coverage threshold enforcement
│       ├── security.sh         ← npm audit / bandit / gosec
│       └── plankton.sh         ← custom / org-specific gate ← wire yours here
│
├── stacked-pr/
│   └── stacked-pr.sh          ← stacked PR orchestrator
│
└── context/
    └── generate-context.sh    ← codebase context generator
```

---

## The Four Phases

### Phase 1: BUILD
The Builder reads the spec and codebase context, then writes code test-first. On cycle 1 it works from the spec. On cycle N > 1 it works from the spec *plus* the structured findings from the previous review.

**Output**: changed files in the worktree.

### Phase 2: VERIFY + FIX (inner loop)
Quality gates run automatically. If any gate fails, the Builder reads the output and makes targeted fixes. This repeats up to `--max-retries` times. Only when all gates pass does the code advance to PUBLISH.

**Gates run**: format → lint → typecheck → tests → coverage → security → plankton → custom

### Phase 3: PUBLISH
Changes are committed with a structured message, pushed to the feature branch, and a PR is created (or updated if one already exists). The PR body is generated from the spec.

### Phase 4: REVIEW
The Reviewer reads the PR diff via `gh pr diff` — it has no access to run code or modify files. It evaluates the diff against the spec's acceptance criteria and outputs a structured findings report.

- **PASS** (zero blockers, zero majors) → workflow exits successfully
- **FAIL** → findings are extracted in `category/severity file:line -- issue -> fix` format and fed to the Builder as the input for the next cycle

---

## Stacked PR Mode

For large features, split the spec into layers. Each layer is an independent PR that builds on the previous one.

```
main
 └── feature/auth-data-model   ← layer 1 (merged first)
      └── feature/auth-service  ← layer 2
           └── feature/auth-api  ← layer 3
                └── feature/auth-ui ← layer 4
```

Define the stack in your spec file:
```yaml
stack:
  - layer: data-model
    branch: feature/auth-data-model
    description: DB schema and migrations
  - layer: service
    branch: feature/auth-service
    description: Business logic
```

Run with `--stack`. The orchestrator runs each layer through the full loop before starting the next. If a layer fails max cycles, the stack stops and you resolve it manually before re-running.

---

## Quality Gates

### Configuring gates

Copy `gates.config.example.sh` → `gates.config.sh` (gitignored) and set:
- `GATE_*=true` to enable a gate
- `COVERAGE_THRESHOLD=N` to set minimum coverage %
- Language-specific commands (`NODE_TEST_CMD`, `PY_LINT_CMD`, etc.)

### Adding a custom gate

1. Create `quality-gates/gates/my-gate.sh` (exit 0 = pass)
2. Add it to `CUSTOM_GATES` array in `gates.config.sh`

### The plankton gate

`plankton.sh` is the designated slot for your org/team's proprietary quality gate. Edit the script to call your tool. Common examples:
- Architecture fitness functions (Deptrac, dependency-cruiser)
- Contract tests (Pact)
- API schema linting (Spectral)
- Compliance checks

---

## Context Engineering

The context generator (`context/generate-context.sh`) produces a structured document given to both Builder and Reviewer before they do any work. It includes:

- Language, framework, and test framework auto-detection
- Depth-limited directory tree (ignores build artifacts)
- Sample source files and test files (first N lines)
- Dependency summary
- Recent git history and active branches
- Contents of `CLAUDE.md` if present

**Best practice**: add a `CLAUDE.md` to every project with:
- Architecture decisions
- Naming conventions
- Patterns to follow (and avoid)
- Known gotchas

---

## Review Findings Format

The Reviewer produces findings in this exact format, which the orchestrator parses:

```
FINDINGS:
[ID-001] category/severity file:line -- Issue -> Fix
[ID-002] category/severity file:line -- Issue -> Fix
END_FINDINGS
VERDICT: FAIL
```

Example:
```
FINDINGS:
[ID-001] security/blocker src/api/users.ts:42 -- Raw SQL with user input -> Use parameterised query
[ID-002] testing/major tests/cart.test.ts:88 -- No test for negative quantity -> Add: should throw when qty < 1
[ID-003] correctness/blocker src/cart/service.ts:61 -- Race condition on concurrent orders -> Wrap in DB transaction
END_FINDINGS
VERDICT: FAIL
```

The Builder addresses each finding by ID in the next cycle.

---

## Session Artifacts

Every run creates `.workflow/sessions/<session-id>/`:

```
sessions/20260228-143022-12345/
├── run.json                  ← metadata
├── codebase-context.md       ← generated context
├── builder-init.md           ← Builder's initial study
├── reviewer-init.md          ← Reviewer's initial study
├── cycle-1/
│   ├── builder-output.md
│   ├── gates-1.log
│   ├── fix-1-output.md
│   ├── gates-2.log
│   ├── reviewer-output.md
│   └── findings.md
└── cycle-2/
    └── ...
```

Add `.workflow/` to `.gitignore`.

---

## Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--max-cycles N` | 3 | Max outer review cycles before giving up |
| `--max-retries N` | 5 | Max inner fix retries before failing a cycle |
| `--stack` | false | Enable stacked PR mode |
| `--base-branch NAME` | main | Branch to base worktree from |
| `--dry-run` | false | Validate only; no commits or PRs |
| `--no-worktree` | false | Skip worktree (use current dir) |
| `--model MODEL` | claude-opus-4-6 | Claude model for agents |

---

## Tips

- **Complex codebases**: add a detailed `CLAUDE.md` — it's included in every agent's context
- **Flaky tests**: increase `--max-retries` and ensure your test suite is deterministic before running the workflow
- **Speed vs quality**: use `claude-sonnet-4-6` for faster/cheaper runs; `claude-opus-4-6` for harder problems
- **Multiple reviewers**: run the same spec twice with different Reviewer prompt variants for cross-check
- **After max cycles**: read the last `findings.md` and resolve blockers manually, then re-run from the current branch state using `--no-worktree`
