from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List


class ScriptKind(str, Enum):
    SERVER = "Script"
    LOCAL = "LocalScript"
    MODULE = "ModuleScript"


class RunContext(str, Enum):
    LEGACY = "Legacy"
    SERVER = "Server"
    CLIENT = "Client"
    PLUGIN = "Plugin"


@dataclass
class ScriptInstance:
    name: str
    kind: ScriptKind
    source: str
    parent_path: str
    disabled: bool = False
    run_context: RunContext = RunContext.LEGACY
    referent: Optional[str] = None
    guid: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    extra_props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InjectionSpec:
    name: str
    kind: ScriptKind
    target_parent: str
    source_file: Optional[Path] = None
    raw_source: Optional[str] = None
    disabled: bool = False
    run_context: RunContext = RunContext.LEGACY
    overwrite: bool = True
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def resolve_source(self, base_dir: Optional[Path] = None) -> str:
        if self.raw_source is not None:
            return self.raw_source
        if self.source_file is None:
            raise ValueError(f"spec '{self.name}' has neither source_file nor raw_source")
        
        p = self.source_file if self.source_file.is_absolute() else (base_dir or Path.cwd()) / self.source_file
        if not p.exists():
            raise FileNotFoundError(f"source script not found: {p}")
        return p.read_text(encoding="utf-8")
