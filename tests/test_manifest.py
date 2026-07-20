import json
import pytest
from roblox_injector.manifest import parse_manifest, ManifestError

def test_parse_valid_manifest(tmp_path):
    manifest_file = tmp_path / "injector.json"
    data = {
        "version": 1,
        "entries": [
            {
                "name": "TestHarness",
                "type": "ServerScript",
                "target": "ServerScriptService/Tests",
                "source": "print('harness loaded')"
            }
        ]
    }
    manifest_file.write_text(json.dumps(data), encoding="utf-8")
    
    manifest = parse_manifest(manifest_file)
    assert len(manifest.entries) == 1
    assert manifest.entries[0].name == "TestHarness"
    assert manifest.entries[0].parent_path == "ServerScriptService/Tests"

def test_missing_required_fields(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"version": 1, "entries": [{"name": "Incomplete"}]}))
    with pytest.raises(ManifestError):
        parse_manifest(f)

def test_unknown_script_type(tmp_path):
    f = tmp_path / "bad_type.json"
    f.write_text(json.dumps({
        "version": 1,
        "entries": [{
            "name": "Bad",
            "type": "UnknownType",
            "target": "Workspace",
            "source": "-- none"
        }]
    }))
    with pytest.raises(ManifestError):
        parse_manifest(f)

def test_resolve_source_file_relative(tmp_path):
    bundle = tmp_path / "bundle.luau"
    bundle.write_text("local M = {}\nreturn M", encoding="utf-8")

    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps({
        "version": 1,
        "entries": [{
            "name": "ClientBundle",
            "type": "ModuleScript",
            "target": "ReplicatedStorage",
            "source_file": "bundle.luau"
        }]
    }), encoding="utf-8")

    manifest = parse_manifest(manifest_file)
    assert "local M = {}" in manifest.entries[0].source

def test_missing_source_file_raises(tmp_path):
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps({
        "version": 1,
        "entries": [{
            "name": "Ghost",
            "type": "ModuleScript",
            "target": "ReplicatedStorage",
            "source_file": "non_existent.luau"
        }]
    }), encoding="utf-8")

    with pytest.raises(ManifestError):
        parse_manifest(manifest_file)
