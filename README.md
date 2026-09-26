# roblox-injector

Command line tool to insert Luau scripts, mocks, and test runners straight into Roblox XML place files (`.rbxlx`) and model files (`.rbxmx`). You don't need Roblox Studio installed or running.

I built this because opening Studio in CI just to bundle analytics wrappers and test harnesses was slow and flaky on headless Linux runners.

## Install

```bash
pip install .
```

Or editable for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

Inject a single ModuleScript into `ReplicatedStorage`:

```bash
rbx-inject inject \
  --input game.rbxlx \
  --output game.injected.rbxlx \
  --target "ReplicatedStorage.Packages" \
  --name "TelemetryBootstrap" \
  --script-type ModuleScript \
  --source ./dist/telemetry.luau
```

Test run without writing files:

```bash
rbx-inject inject --input game.rbxlx --manifest inject.json --dry-run
```

## Manifest Files

If you have multiple scripts (like a test runner, some mocks, and an entrypoint script), define them in a JSON manifest:

```json
{
  "injections": [
    {
      "target_path": "ServerScriptService.Tests",
      "name": "Runner",
      "class_name": "Script",
      "source_file": "build/ci_runner.luau",
      "properties": {
        "RunContext": "Server",
        "Disabled": false
      }
    },
    {
      "target_path": "ReplicatedStorage.Telemetry",
      "name": "ClientShim",
      "class_name": "LocalScript",
      "source_file": "dist/shim.luau",
      "overwrite": true
    }
  ]
}
```

Run with the manifest:

```bash
rbx-inject batch --input place.rbxlx --manifest inject.json --output place.ci.rbxlx
```

Target paths create missing `Folder` instances automatically if they don't exist yet.

<!-- checked: 2026-09-26 -->
