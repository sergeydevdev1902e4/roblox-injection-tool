import hashlib
import random
from typing import Set, Optional


class ReferentGenerator:
    """Generates unique RBX referent attributes without colliding with existing place nodes."""

    def __init__(self, existing_referents: Optional[Set[str]] = None, prefix: str = "RBX"):
        self._used: Set[str] = set()
        if existing_referents:
            for r in existing_referents:
                if r and isinstance(r, str):
                    self._used.add(r.strip())
        self._prefix = prefix
        self._counter = 0

    def track(self, referent: Optional[str]) -> None:
        if referent:
            self._used.add(referent.strip())

    def generate(self, seed_name: str = "") -> str:
        if seed_name:
            # deterministic hash helps keep git diffs tidy when re-injecting same tree
            self._counter += 1
            payload = f"{seed_name}_{self._counter}".encode("utf-8")
            raw = hashlib.md5(payload).hexdigest().upper()
            ref = f"{self._prefix}{raw[:16]}"
            if ref not in self._used:
                self._used.add(ref)
                return ref

        while True:
            rnd = random.getrandbits(64)
            ref = f"{self._prefix}{rnd:016X}"
            if ref not in self._used:
                self._used.add(ref)
                return ref

    def next_indexed(self) -> str:
        # Some older tooling prefers RBX0, RBX1 sequence
        while True:
            ref = f"{self._prefix}{self._counter}"
            self._counter += 1
            if ref not in self._used:
                self._used.add(ref)
                return ref
