#!/usr/bin/env python3
"""Bind an actual visual-review receipt to the exact spec and proof bytes.

Primary source: gsh4124-cyber/hwangje-vault/tools/global_shorts/proof_gate.py.
This validates the receipt; it does not perform or replace visual QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROOF_FILES = ("hook.png", "challenge.png", "reveal.png", "contact_sheet.png")
COMMON_GATES = ("HOOK_CLARITY", "PAYOFF_CLARITY", "VISUAL_QUALITY", "NOVELTY")
ODD_ONE_OUT_GATES = (
    "RULE_CLARITY", "UNIQUE_ANSWER", "SEARCHABILITY", "FAIRNESS",
    "DISTRACTOR_QUALITY", "REVEAL_CLARITY", "MOBILE_READABILITY", "SUBSTANTIVE_NOVELTY",
)


class ProofGateError(ValueError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(spec_path: Path, proof_dir: Path, receipt_path: Path, receipt_root: Path | None = None) -> dict:
    if receipt_root is not None and not receipt_path.resolve().is_relative_to(receipt_root.resolve()):
        raise ProofGateError("Review receipt must remain inside the committed QA directory")
    if not receipt_path.is_file():
        raise ProofGateError("Missing committed actual-artifact Proof QA receipt")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("decision") != "PASS":
        raise ProofGateError("Proof QA is not PASS; full render is forbidden")
    if receipt.get("review_method") != "ACTUAL_ARTIFACT_VISUAL_REVIEW":
        raise ProofGateError("Generated manifest or self-report cannot approve full render")
    reviewer = receipt.get("reviewer")
    if not isinstance(reviewer, dict) or reviewer.get("kind") not in ("assistant", "human") or not reviewer.get("id"):
        raise ProofGateError("Identified actual-artifact reviewer is required")
    try:
        reviewed_at = datetime.fromisoformat(receipt["reviewed_at"].replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None or reviewed_at > datetime.now(timezone.utc):
            raise ValueError("Invalid review time")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ProofGateError("Past timezone-aware actual review time is required") from exc
    if not spec.get("episode_id") or receipt.get("episode_id") != spec["episode_id"]:
        raise ProofGateError("Receipt belongs to a different episode")
    if receipt.get("spec_sha256") != digest(spec_path):
        raise ProofGateError("Spec changed after review; new proof review is required")
    if spec.get("format") != "odd_one_out":
        raise ProofGateError("This reference gate supports odd_one_out only")
    gates = receipt.get("gates")
    if not isinstance(gates, dict):
        raise ProofGateError("All common and format-specific QA findings are required")
    for name in COMMON_GATES + ODD_ONE_OUT_GATES:
        finding = gates.get(name)
        if not isinstance(finding, dict) or finding.get("result") != "PASS" or not isinstance(finding.get("finding"), str) or not finding["finding"].strip():
            raise ProofGateError(f"Missing or non-PASS actual visual finding: {name}")
    reviewed_files = receipt.get("reviewed_files")
    if not isinstance(reviewed_files, dict) or set(reviewed_files) != set(PROOF_FILES):
        raise ProofGateError("Review must cover hook, challenge, reveal, and contact sheet")
    evidence = receipt.get("artifact_review_evidence")
    if not isinstance(evidence, dict) or set(evidence) != set(PROOF_FILES):
        raise ProofGateError("Actual file-open/review evidence is required for each proof file")
    for name in PROOF_FILES:
        path = proof_dir / name
        if not path.is_file() or not path.stat().st_size or reviewed_files[name] != digest(path):
            raise ProofGateError(f"Proof missing or changed after review: {name}")
        item = evidence[name]
        if not isinstance(item, dict) or not item.get("method") or not item.get("reference"):
            raise ProofGateError(f"Actual review evidence is missing: {name}")
    return {"episode_id": spec["episode_id"], "spec_sha256": digest(spec_path), "decision": "PASS_RECEIPT_VALIDATED", "visual_qa_performed_by_this_script": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--receipt-root", type=Path)
    args = parser.parse_args()
    receipt_root = args.receipt_root or args.spec.parent.parent / "qa"
    print(json.dumps(validate(args.spec, args.proof, args.receipt, receipt_root), ensure_ascii=False))


if __name__ == "__main__":
    main()
