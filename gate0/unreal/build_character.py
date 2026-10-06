"""
Gate 0 step 1 — assemble a MetaHuman Character asset into a usable actor.

A MetaHuman Character asset is editable data, not something you can put in a scene. Assembling
("building") it produces a Blueprint with the skeletal meshes, materials and grooms, which is
what a Level Sequence can film.

Run in the Unreal Editor Output Log:

    py "/Users/na/FilmMaker/gate0/unreal/build_character.py" check      # is it rigged / buildable?
    py "/Users/na/FilmMaker/gate0/unreal/build_character.py" rig        # request auto-rig (Epic cloud)
    py "/Users/na/FilmMaker/gate0/unreal/build_character.py" build      # assemble at cinematic quality

'check' changes nothing. Run it first; it says whether 'rig' is needed before 'build'.
Auto-rigging calls Epic's cloud service, so you must be signed in to your Epic account in the
editor, and it takes ~1 minute.

Output of 'build': /Game/MetaHumans/<name>/BP_<name>  (plus meshes and materials beside it)
"""
import sys
import unreal

ASSET = "/Game/alice"
BUILD_ROOT = "/Game/MetaHumans"


def log(m):
    unreal.log(f"[build_character] {m}")


def character():
    c = unreal.EditorAssetLibrary.load_asset(ASSET)
    if not c:
        raise SystemExit(f"[build_character] asset not found: {ASSET}")
    return c


def sub():
    return unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)


def check():
    s, c = sub(), character()
    log(f"character: {c.get_name()}")
    log(f"  has_high_resolution_textures: {c.has_high_resolution_textures()}")
    buildable = s.can_build_meta_human(c, log_error=True)
    log(f"  can_build_meta_human: {buildable}")
    if not buildable:
        log("  -> run 'rig' first (and/or 'textures' if it complains about textures)")
    return buildable


def rig():
    s, c = sub(), character()
    log("requesting auto-rig from Epic's cloud service (joints + blend shapes, blocking)...")
    params = unreal.MetaHumanCharacterAutoRiggingRequestParams(
        rig_type=unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES,
        report_progress=True,
        blocking=True,
    )
    with_edit(s, c, lambda: s.request_auto_rigging(c, params))
    unreal.EditorAssetLibrary.save_asset(ASSET)
    log("auto-rig finished; asset saved. Run 'check' again.")


def textures():
    s, c = sub(), character()
    log("requesting texture sources (Epic cloud, blocking)...")
    params = unreal.MetaHumanCharacterTextureRequestParams(b_report_progress=True, b_blocking=True)
    with_edit(s, c, lambda: s.request_texture_sources(c, params))
    unreal.EditorAssetLibrary.save_asset(ASSET)
    log("textures finished; asset saved.")


def with_edit(s, c, fn):
    added = False
    if not s.is_object_added_for_editing(c):
        if not s.try_add_object_to_edit(c):
            raise SystemExit("[build_character] could not add character for editing")
        added = True
    try:
        return fn()
    finally:
        if added:
            s.remove_object_to_edit(c)


def build():
    s, c = sub(), character()
    if not s.can_build_meta_human(c, log_error=True):
        raise SystemExit("[build_character] not buildable yet — run 'check' to see why")
    params = unreal.MetaHumanCharacterEditorBuildParameters(
        pipeline_type=unreal.MetaHumanDefaultPipelineType.CINEMATIC,
        pipeline_quality=unreal.MetaHumanQualityLevel.CINEMATIC,
        common_folder_path=f"{BUILD_ROOT}/Common",
    )
    log(f"building {c.get_name()} (cinematic pipeline, cinematic quality) into {BUILD_ROOT} ...")
    with_edit(s, c, lambda: s.build_meta_human(c, params))
    log("build call returned. Assets under the build root:")
    for p in unreal.EditorAssetLibrary.list_assets(BUILD_ROOT, recursive=True, include_folder=False):
        log(f"  {p}")


if __name__ == "__main__":
    arg = (sys.argv[1] if len(sys.argv) > 1 else "check").lower()
    {"check": check, "rig": rig, "build": build, "textures": textures}.get(
        arg, lambda: log("usage: check | rig | textures | build")
    )()
