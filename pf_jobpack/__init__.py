"""Core, runtime-agnostic logic for the TCO job-pack flow.

This package contains pure Python only (no ``promptflow`` dependency) so the
same logic can be driven by the current Prompt Flow DAG (via the thin adapters
in ``nodes/``) and, later, by the Microsoft Agent Framework migration.

Module map (mirrors the original Prompt Flow nodes):

- ``extraction``  -> scope-field extraction (``build_scope_json_from_input``)
- ``state``       -> conversation state: load / merge / validate / route
- ``search``      -> Azure AI Search query building + HTTP client
- ``pwht``        -> post-weld heat-treatment flag evaluation
- ``nde``         -> NDE lookup evaluation
- ``material``    -> material (CS/SS) classification
- ``template``    -> job-pack text assembly
"""
