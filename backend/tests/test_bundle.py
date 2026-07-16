from pathlib import Path

import pytest

from backend.app.services.bundle import BundleError, validate_bundle


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_bundle"


def test_synthetic_bundle_manifest_checksum_and_rows():
    result = validate_bundle(FIXTURE)
    assert result.manifest.synthetic is True
    assert len(result.records["teams"]) == 4
    assert result.warnings == []


def test_bundle_rejects_path_traversal(tmp_path):
    (tmp_path / "manifest.json").write_text('{"format_version":"1","dataset_name":"x","dataset_version":"1","provider":"x","generated_at":"x","files":[{"path":"../outside.jsonl","rows":0,"sha256":"' + "0" * 64 + '","schema_fingerprint":"x"}],"generating_tool_version":"x"}')
    with pytest.raises(BundleError, match="path traversal"):
        validate_bundle(tmp_path)


def test_bundle_rejects_checksum_mismatch(tmp_path):
    (tmp_path / "teams.jsonl").write_text('{}\n')
    (tmp_path / "manifest.json").write_text('{"format_version":"1","dataset_name":"x","dataset_version":"1","provider":"x","generated_at":"x","files":[{"path":"teams.jsonl","rows":1,"sha256":"' + "0" * 64 + '","schema_fingerprint":"x"}],"generating_tool_version":"x"}')
    with pytest.raises(BundleError, match="checksum mismatch"):
        validate_bundle(tmp_path)
