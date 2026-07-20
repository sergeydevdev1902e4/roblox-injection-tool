import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

from roblox_injector.models import InjectionSpec, ScriptKind, RunContext


def _parse_kind(raw: str) -> ScriptKind:
    val = raw.strip().lower()
    if val in ("script", "server"):
        return ScriptKind.SERVER
    if val in ("localscript", "client", "local"):
        return ScriptKind.LOCAL
    if val in ("modulescript", "module"):
        return ScriptKind.MODULE
    raise ValueError(f"unknown script kind: {raw}")


def _parse_run_context(raw: Optional[str] = None) -> RunContext:
    if not raw:
        return RunContext.LEGACY
    val = str(raw).strip().lower()
    if val in ("server", "runcontext.server"):
        return RunContext.SERVER
    if val in ("client", "runcontext.client"):
        return RunContext.CLIENT
    if val in ("plugin", "runcontext.plugin"):
        return RunContext.PLUGIN
    if val in ("legacy", "runcontext.legacy"):
        return RunContext.LEGACY
    return RunContext.LEGACY


def _spec_from_dict(d: Dict[str, Any], manifest_dir: Path) -> InjectionSpec:
    if "name" not in d:
        raise KeyError("manifest entry missing required 'name' field")
    if "target" not in d and "target_parent" not in d:
        raise KeyError(f"entry '{d['name']}' missing 'target' parent path")

    target = d.get("target") or d.get("target_parent")
    kind_str = d.get("kind", d.get("type", "ModuleScript"))
    kind = _parse_kind(str(kind_str))
    
    rc = _parse_run_context(d.get("run_context"))

    src_file = None
    if "source_file" in d:
        src_file = Path(d["source_file"])
    elif "file" in d:
        src_file = Path(d["file"])
    elif "path" in d:
        src_file = Path(d["path"])

    if src_file and not src_file.is_absolute():
        src_file = manifest_dir / src_file

    return InjectionSpec(
        name=str(d["name"]),
        kind=kind,
        target_parent=str(target),
        source_file=src_file,
        raw_source=d.get("source"),
        disabled=bool(d.get("disabled", False)),
        run_context=rc,
        overwrite=bool(d.get("overwrite", True)),
        tags=d.get("tags", []),
        properties=d.get("properties", {})
    )


def load_manifest(path: Union[str, Path]) -> List[InjectionSpec]:
    """Load an injection manifest from a JSON or TOML file."""
    manifest_path = Path(path).resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest file not found: {manifest_path}")

    text = manifest_path.read_text(encoding="utf-8")
    if manifest_path.suffix.lower() == ".json":
        data = json.loads(text)
    elif manifest_path.suffix.lower() in (".toml", ".tml"):
        data = tomllib.loads(text)
    else:
        try:
            data = json.loads(text)
        except Exception:
            data = tomllib.loads(text)

    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "scripts" in data:
            items = data["scripts"]
        elif "inject" in data:
            items = data["inject"]
        else:
            if "name" in data:
                items = [data]
            else:
                # TOML sections like [bundle_a], [bundle_b]
                items = []
                for k, v in data.items():
                    if isinstance(v, dict):
                        if "name" not in v:
                            v["name"] = k
                        items.append(v)

    manifest_dir = manifest_path.parent
    return [_spec_from_dict(item, manifest_dir) for item in items]
