"""
Gate 0 — apply a life stage from alice.yaml to a MetaHuman Character asset.

This is the "chat -> outcome" path: the yaml is the spec, this script does the clicking.
It uses the same MetaHumanCharacterEditorSubsystem API the editor buttons call.

Run inside the Unreal Editor. Output Log -> switch the command box to "Python" (or prefix with
`py`), then:

    py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" old
    py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" middle
    py "/Users/na/FilmMaker/gate0/unreal/apply_stage.py" dump      # print landmark + body info

What it does for a stage:
  1. duplicates /Game/alice -> /Game/alice_<stage>  (base is never modified)
  2. body: resolves the stage's proportions_cm (numbers or "young + 4" / "young * 0.96"
     expressions against the base's current measurements) and sets the parametric constraints
  3. skin: roughness delta and face texture index
  4. face: first-pass aging by translating landmark regions (cheeks down, mouth corners down,
     lips thinner). Symmetric per side, so the base's asymmetries are preserved.
  5. saves the asset and prints what it changed

Then open alice_<stage> in the editor and judge it. Adjust the yaml, re-run.
Close the editor tab of the stage asset you are re-creating before running (the script refuses
otherwise). Other tabs, including the base, may stay open; dump is read-only and works either way.
"""
import re, sys, os
import unreal

YAML_PATH = "/Users/na/FilmMaker/gate0/character/alice.yaml"
BASE_ASSET = "/Game/alice"
ASSET_DIR = "/Game"

# Body constraint names as MetaHuman reports them (tooltip keys). Anything in the yaml that
# isn't a real constraint name is reported and skipped.
BODY_ALIASES = {
    "Height": "Height", "AcrossShoulder": "Across Shoulder", "Chest": "Chest", "Waist": "Waist",
    "Hip": "Hip", "HighHip": "High Hip", "HandCircumference": "Hand Circumference",
    "NeckLength": "Neck Length", "Neck": "Neck", "NeckBase": "Neck Base",
    "UpperArmLength": "Upper Arm Length", "LowerArmLength": "Lower Arm Length",
    "ShoulderHeight": "Shoulder Height", "Fat": "Fat", "Muscularity": "Muscularity",
}

# Face landmark regions for first-pass aging. Landmarks are selected by position relative to the
# face's own bounding box (x = left/right, z = up/down in MetaHuman's face space). Tune after
# running `dump` once and looking at the printed extents.
#   fraction ranges are of the face bbox: x in [-1, 1] (0 = midline), z in [0, 1] (0 = chin)
AGING_REGIONS = {
    # name: (x_abs_min, x_abs_max, z_min, z_max, delta_cm (x, y, z))
    # deltas are cm at strength 1.0 (old). Deliberately bold so the change is unmistakable;
    # dial back once the loop is confirmed visually.
    "cheeks":        (0.35, 0.80, 0.35, 0.60, (0.0, 0.0, -1.20)),
    "jowls":         (0.30, 0.70, 0.10, 0.30, (0.4, 0.0, -1.00)),   # down and slightly outward
    "mouth_corners": (0.15, 0.40, 0.26, 0.40, (0.0, 0.0, -0.50)),
    "upper_lip":     (0.00, 0.18, 0.33, 0.38, (0.0, 0.0, -0.15)),
}
AGING_STRENGTH = {"young": 0.0, "middle": 0.45, "old": 1.0, "extreme": 2.5}


def load_yaml():
    import yaml
    with open(YAML_PATH) as f:
        return yaml.safe_load(f)


def log(msg):
    unreal.log(f"[apply_stage] {msg}")


def resolve(expr, base):
    """'young + 4', 'young * 0.96', 'young', 'preset_default', or a number."""
    if isinstance(expr, (int, float)):
        return float(expr)
    s = str(expr).strip()
    if s in ("preset_default", "young", "none"):
        return base
    m = re.fullmatch(r"young\s*([+\-*/])\s*([0-9.]+)", s)
    if m:
        op, v = m.group(1), float(m.group(2))
        return {"+": base + v, "-": base - v, "*": base * v, "/": base / v}[op]
    raise ValueError(f"cannot resolve body expression {expr!r}")


def get_subsystem():
    return unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)


def refuse_if_open(sub, character):
    # Adding/removing edit state on a character that has an open editor tab crashes UE 5.8
    # (the tab's tools lose their target). Only the asset we are about to MODIFY must be closed.
    if sub.is_object_added_for_editing(character):
        raise SystemExit(f"[apply_stage] REFUSING TO RUN: '{character.get_name()}' has an open editor tab. Close it, then re-run.")


class EditSession:
    """Add a character for editing only if it isn't already; remove only what we added."""
    def __init__(self, sub, character):
        self.sub, self.c, self.added = sub, character, False
    def __enter__(self):
        if not self.sub.is_object_added_for_editing(self.c):
            if not self.sub.try_add_object_to_edit(self.c):
                raise RuntimeError("could not add character for editing")
            self.added = True
        return self.c
    def __exit__(self, *exc):
        if self.added:
            self.sub.remove_object_to_edit(self.c)


def load_character(path):
    c = unreal.EditorAssetLibrary.load_asset(path)
    if not c:
        raise RuntimeError(f"asset not found: {path}")
    return c


def constraints_by_name(sub, character):
    out = {}
    for c in sub.get_body_constraints(character):
        out[str(c.name)] = c
    return out


def apply_body(sub, character, stage_props, base_props):
    cons = constraints_by_name(sub, character)
    base_vals = {n: float(c.target_measurement) for n, c in cons.items()}
    changed = []
    for key, expr in (stage_props or {}).items():
        name = BODY_ALIASES.get(key, key)
        if name not in cons:
            log(f"  body: '{key}' is not a MetaHuman body constraint — skipped. Known: {sorted(cons)}")
            continue
        target = resolve(expr, base_vals[name])
        c = cons[name]
        lo, hi = float(c.min_measurement), float(c.max_measurement)
        clamped = max(lo, min(hi, target))
        if abs(clamped - base_vals[name]) < 1e-3:
            continue
        c.is_active = True
        c.target_measurement = clamped
        changed.append(f"{name}: {base_vals[name]:.1f} -> {clamped:.1f}" + (" (clamped)" if clamped != target else ""))
    if changed:
        sub.set_body_constraints(character, list(cons.values()))
        sub.commit_body_state(character)
    for line in changed:
        log(f"  body: {line}")
    return changed


def apply_skin(sub, character, face):
    ss = character.get_editor_property("skin_settings")
    skin = ss.get_editor_property("skin")
    changed = []
    r = face.get("skin_roughness", "preset_default")
    cur = float(skin.get_editor_property("roughness"))
    new = max(0.85, min(1.15, resolve(r, cur)))
    if abs(new - cur) > 1e-4:
        skin.set_editor_property("roughness", new)
        changed.append(f"roughness {cur:.3f} -> {new:.3f}")
    tex = face.get("skin_face_texture_index")
    if isinstance(tex, int):
        old = int(skin.get_editor_property("face_texture_index"))
        if tex != old:
            skin.set_editor_property("face_texture_index", tex)
            changed.append(f"face_texture_index {old} -> {tex}")
    if changed:
        ss.set_editor_property("skin", skin)
        sub.commit_skin_settings(character, ss)
    for line in changed:
        log(f"  skin: {line}")
    return changed


def face_bbox(landmarks):
    xs = [p.x for p in landmarks]; zs = [p.z for p in landmarks]
    return min(xs), max(xs), min(zs), max(zs)


def apply_face_aging(sub, character, strength):
    if strength <= 0:
        return []
    lms = sub.get_face_landmarks(character)
    if not lms:
        log("  face: no landmarks returned — is the character added for edit?")
        return []
    x0, x1, z0, z1 = face_bbox(lms)
    half_w = max(abs(x0), abs(x1)); h = (z1 - z0) or 1.0
    idx, deltas, summary = [], [], []
    for name, (xa, xb, za, zb, d) in AGING_REGIONS.items():
        n = 0
        for i, p in enumerate(lms):
            fx = abs(p.x) / half_w if half_w else 0.0
            fz = (p.z - z0) / h
            if xa <= fx <= xb and za <= fz <= zb:
                idx.append(i)
                deltas.append(unreal.Vector(d[0] * strength, d[1] * strength, d[2] * strength))
                n += 1
        summary.append(f"{name}:{n}")
    if idx:
        sub.translate_face_landmarks(character, idx, deltas)
        sub.commit_face_state(character)
    log(f"  face: aging strength {strength:.2f}, landmarks moved per region: {', '.join(summary)}")
    return summary


def dump(asset=None):
    sub = get_subsystem()
    path = f"{ASSET_DIR}/{asset}" if asset else BASE_ASSET
    log(f"dumping {path}")
    c = load_character(path)
    session = EditSession(sub, c); session.__enter__()
    log(f"body constraints on {path}:")
    for n, k in sorted(constraints_by_name(sub, c).items()):
        log(f"  {n:22s} {float(k.target_measurement):8.2f}  [{float(k.min_measurement):.1f} .. {float(k.max_measurement):.1f}]  active={bool(k.is_active)}")
    skin = c.get_editor_property("skin_settings").get_editor_property("skin")
    log(f"skin: roughness={float(skin.get_editor_property('roughness')):.3f} face_texture_index={int(skin.get_editor_property('face_texture_index'))} body_texture_index={int(skin.get_editor_property('body_texture_index'))}")
    lms = sub.get_face_landmarks(c)
    x0, x1, z0, z1 = face_bbox(lms)
    log(f"face landmarks: {len(lms)}  x[{x0:.2f},{x1:.2f}] z[{z0:.2f},{z1:.2f}]")
    for i, p in enumerate(lms):
        log(f"  lm{i:03d}  x={p.x:7.2f} y={p.y:7.2f} z={p.z:7.2f}")
    session.__exit__(None, None, None)


def run(stage):
    spec = load_yaml()
    if stage not in spec["stages"]:
        raise SystemExit(f"stage must be one of {list(spec['stages'])}")
    st = spec["stages"][stage]
    target = f"{ASSET_DIR}/alice_{stage}"
    sub = get_subsystem()

    if unreal.EditorAssetLibrary.does_asset_exist(target):
        refuse_if_open(sub, load_character(target))
        log(f"{target} exists — deleting and re-creating from base")
        unreal.EditorAssetLibrary.delete_asset(target)
    if not unreal.EditorAssetLibrary.duplicate_asset(BASE_ASSET, target):
        raise RuntimeError("duplicate failed")
    log(f"duplicated {BASE_ASSET} -> {target}")

    c = load_character(target)
    with EditSession(sub, c):
        log(f"stage '{stage}': age {st.get('age')}")
        apply_body(sub, c, st.get("proportions_cm"), spec["stages"]["young"].get("proportions_cm"))
        apply_skin(sub, c, st.get("face", {}))
        apply_face_aging(sub, c, AGING_STRENGTH.get(stage, 0.0))
        cons = st.get("constraints") or {}
        if cons:
            log(f"  constraints {cons} recorded in yaml; the stoop is applied at animation time, not on the character asset")
    unreal.EditorAssetLibrary.save_asset(target)
    log(f"saved {target}. Open it in the Content Drawer to judge; edit the yaml and re-run to iterate.")


if __name__ == "__main__":
    arg = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if arg == "dump":
        dump(sys.argv[2] if len(sys.argv) > 2 else None)
    elif arg:
        run(arg)
    else:
        log("usage: py apply_stage.py <young|middle|old|dump>")
