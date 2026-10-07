"""Regression cases for the previously missing Proof-to-full interlock.

Fixture bytes test approval binding only; they are not visual proofs or QA PASS.
"""
import json
import tempfile
import unittest
from pathlib import Path
from proof_gate import COMMON_GATES, ODD_ONE_OUT_GATES, PROOF_FILES, ProofGateError, digest, validate


class ProofGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.spec = self.root / "spec.json"
        self.spec.write_text(json.dumps({"episode_id": "TEST-001", "format": "odd_one_out"}))
        self.proof = self.root / "proof"
        self.proof.mkdir()
        for name in PROOF_FILES:
            (self.proof / name).write_bytes(b"NON_MEDIA_TEST_FIXTURE_" + name.encode())
        self.receipt_path = self.root / "qa.json"
        self.receipt = {
            "decision": "PASS", "review_method": "ACTUAL_ARTIFACT_VISUAL_REVIEW",
            "reviewer": {"kind": "assistant", "id": "TEST_ONLY"},
            "reviewed_at": "2026-01-01T00:00:00Z", "episode_id": "TEST-001",
            "spec_sha256": digest(self.spec),
            "gates": {k: {"result": "PASS", "finding": "TEST_ONLY_NOT_ACTUAL_VISUAL_QA"} for k in COMMON_GATES + ODD_ONE_OUT_GATES},
            "reviewed_files": {n: digest(self.proof / n) for n in PROOF_FILES},
            "artifact_review_evidence": {n: {"method": "TEST_ONLY", "reference": "fixture:" + n} for n in PROOF_FILES},
        }

    def run_gate(self):
        self.receipt_path.write_text(json.dumps(self.receipt))
        return validate(self.spec, self.proof, self.receipt_path)

    def test_review_receipt_for_same_bytes_validates_without_claiming_visual_qa(self):
        self.assertFalse(self.run_gate()["visual_qa_performed_by_this_script"])

    def test_missing_receipt_blocks_full_render(self):
        with self.assertRaises(ProofGateError):
            validate(self.spec, self.proof, self.receipt_path)

    def test_fail_or_unknown_decision_blocks(self):
        for decision in ("FAIL", "UNKNOWN", "ARTIFACT_READY_FOR_VISUAL_QA"):
            with self.subTest(decision=decision):
                self.receipt["decision"] = decision
                with self.assertRaises(ProofGateError): self.run_gate()

    def test_self_report_manifest_is_not_a_review(self):
        self.receipt["review_method"] = "GENERATED_MANIFEST"
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_changed_spec_invalidates_approval(self):
        self.spec.write_text(json.dumps({"episode_id": "TEST-001", "format": "odd_one_out", "answer_index": 3}))
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_other_episode_cannot_reuse_receipt(self):
        self.receipt["episode_id"] = "TEST-002"
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_each_modified_proof_file_blocks(self):
        for name in PROOF_FILES:
            with self.subTest(file=name):
                path = self.proof / name
                original = path.read_bytes()
                path.write_bytes(original + b"changed")
                with self.assertRaises(ProofGateError): self.run_gate()
                path.write_bytes(original)

    def test_missing_file_blocks(self):
        (self.proof / "reveal.png").unlink()
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_partial_review_blocks(self):
        del self.receipt["reviewed_files"]["hook.png"]
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_review_open_evidence_is_required(self):
        self.receipt["artifact_review_evidence"] = {}
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_all_required_gates_must_pass_with_findings(self):
        for name in COMMON_GATES + ODD_ONE_OUT_GATES:
            with self.subTest(gate=name):
                self.receipt["gates"][name] = {"result": "UNKNOWN", "finding": "unverified"}
                with self.assertRaises(ProofGateError): self.run_gate()
                self.receipt["gates"][name] = {"result": "PASS", "finding": "TEST_ONLY"}

    def test_unsupported_format_is_not_approved(self):
        self.spec.write_text(json.dumps({"episode_id": "TEST-001", "format": "logic_puzzle"}))
        self.receipt["spec_sha256"] = digest(self.spec)
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_future_review_timestamp_is_not_evidence(self):
        self.receipt["reviewed_at"] = "2999-01-01T00:00:00Z"
        with self.assertRaises(ProofGateError): self.run_gate()

    def test_receipt_path_cannot_escape_committed_qa_directory(self):
        self.run_gate()
        with self.assertRaises(ProofGateError):
            validate(self.spec, self.proof, self.receipt_path, self.root / "qa")

    def test_receipt_symlink_cannot_escape_qa_directory(self):
        self.run_gate()
        qa = self.root / "qa"
        qa.mkdir()
        link = qa / "receipt.json"
        link.symlink_to(self.receipt_path)
        with self.assertRaises(ProofGateError):
            validate(self.spec, self.proof, link, qa)


if __name__ == "__main__":
    unittest.main()
