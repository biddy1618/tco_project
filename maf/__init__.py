"""Microsoft Agent Framework migration slices.

Prompt Flow under the repo root stays the source of truth until a slice is
parity-checked. Each ``sliceN`` module is a small WorkflowBuilder graph that
reuses ``pf_jobpack`` for Python logic.
"""
