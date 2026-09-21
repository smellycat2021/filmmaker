# Gate 0 — Unreal commands cheat sheet

Everything here is typed into the Unreal Editor's **Output Log** command box
(**Window → Output Log**, the "Enter Console Command" field at the bottom).
The `py` prefix runs the rest of the line as Python.

## Launch the editor on this project (Terminal, not Unreal)

```
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "/Users/na/FilmMaker/gate0/unreal/Gate0/Gate0.uproject"
```

Epic Games Launcher must be started natively or it crashes on macOS 27:

```
open --arch arm64 -a "Epic Games Launcher"
```

## Character stages (apply_stage.py)

Reads `gate0/character/alice.yaml`. The base asset `MHC_Alice_Base` is never modified;
each stage is created as a fresh duplicate `MHC_Alice_<Stage>`. Close the asset's editor tab
before running — the script can't edit an asset that's open.

| Command | What it does |
| --- | --- |
| `py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" dump` | Print the base's body measurements, skin values, and face landmarks. Changes nothing. |
| `py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" young` | Create `MHC_Alice_Young` (= base, no changes). |
| `py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" middle` | Create `MHC_Alice_Middle` with the middle-age deltas. |
| `py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" old` | Create `MHC_Alice_Old` with the old-age deltas. |

Iterate: open the stage asset in the Content Drawer → judge → edit `alice.yaml` → re-run the
same command (it deletes and re-creates the stage asset from the base).

## Rendering (render_passes.py) — later, once a Level Sequence exists

```
py "/Users/na/FilmMaker/gate0/unreal/render_passes.py"
```

Then in the same box:

```
py import render_passes; render_passes.render("/Game/Gate0/Seq_Alice_Young", "young")
```

Outputs EXR sequences to `gate0/renders/<stage>/`.

## Where things are

| | Path |
| --- | --- |
| Character spec (the source of truth) | `gate0/character/alice.yaml` |
| Unreal project | `gate0/unreal/Gate0/Gate0.uproject` |
| Editor log (for reading script output) | `~/Library/Logs/Unreal Engine/Gate0Editor/Gate0.log` |
| MetaHuman presets (engine, after Core Data install) | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Optional/Presets` |

## Editor UI notes (MetaHuman Character editor, UE 5.8)

- **Presets** — top-level toolbar button. Double-click a tile or right-click → Apply Preset.
- **Head & Body → Body Params → Parametric** — cm measurement fields.
- **Head & Body → Head Transform / Head Sculpt** — face edits. In the tool's details panel,
  **Manipulators → Symmetric Manipulation** toggles one-sided vs mirrored edits.
- **Materials → Skin** — face texture choice and Roughness (0.85–1.15). There is no "age" slider;
  aging = texture + roughness + sculpt + hair.
- Content Drawer: **Ctrl+Space**.
