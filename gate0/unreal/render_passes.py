"""
Gate 0 — Movie Render Queue render with structural passes.

Run inside the Unreal Editor (Python console, or `-ExecutePythonScript`) after the scene,
Level Sequence, and cine camera exist. Renders one stage; call once per stage with a different
sequence / output folder.

    import render_passes; render_passes.render("/Game/Gate0/Seq_Alice_Young", "young")

Outputs to gate0/renders/<stage>/ as an EXR sequence with these layers:
    FinalImage      RGB (Lumen)
    WorldDepth      depth — MRQ ships this post-process material
    MotionVectors   MRQ ships this post-process material
    WorldNormal     MRQ ships this post-process material (5.8)
    ObjectId        segmentation, via the Object Ids render pass

Then `ffmpeg` the FinalImage layer to an mp4 for the viewers, and keep the EXRs for
conditioning the generative step.

Written for UE 5.8.2.
"""
import unreal

WORLD_NORMAL_MATERIAL = "/MovieRenderPipeline/Materials/MovieRenderQueue_WorldNormal"

# Project lives at gate0/unreal/Gate0/, renders go to gate0/renders/. MRQ expands {project_dir}.
OUT_ROOT = "{project_dir}/../../renders"


def render(sequence_path: str, stage: str, resolution=(1920, 1080), fps=24):
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    queue = subsystem.get_queue()
    queue.delete_all_jobs()

    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.sequence = unreal.SoftObjectPath(sequence_path)
    job.map = unreal.SoftObjectPath(unreal.EditorLevelLibrary.get_editor_world().get_path_name())
    job.job_name = f"gate0_{stage}"

    cfg = job.get_configuration()

    # Output: multilayer EXR so every pass lands in one file per frame.
    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out.output_directory = unreal.DirectoryPath(f"{OUT_ROOT}/{stage}")
    out.file_name_format = "{sequence_name}.{frame_number}"
    out.output_resolution = unreal.IntPoint(*resolution)
    out.output_frame_rate = unreal.FrameRate(fps, 1)
    out.override_existing_output = True

    exr = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
    exr.multilayer = True

    # Main deferred pass + post-process material passes.
    deferred = cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    deferred.disable_multisample_effects = True  # crisper structural passes; no TAA smear
    mats = []
    for path in [
        "/MovieRenderPipeline/Materials/MovieRenderQueue_WorldDepth",
        "/MovieRenderPipeline/Materials/MovieRenderQueue_MotionVectors",
        WORLD_NORMAL_MATERIAL,
    ]:
        if not path:
            continue
        m = unreal.MoviePipelinePostProcessPass()
        m.enabled = True
        m.material = unreal.SoftObjectPath(path)
        mats.append(m)
    deferred.additional_post_process_materials = mats

    # Object Id (segmentation) pass.
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineObjectIdRenderPass)

    # Anti-aliasing: temporal samples for the RGB, keep it modest so passes stay aligned.
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.spatial_sample_count = 1
    aa.temporal_sample_count = 8
    aa.override_anti_aliasing = True
    aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_TSR

    # Lumen: make sure the console vars match the look you judged in-editor.
    cvars = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    cvars.console_variables = {
        "r.Lumen.Reflections.Allow": 1,
        "r.DynamicGlobalIlluminationMethod": 1,  # Lumen
        "r.ReflectionMethod": 1,                 # Lumen
        "r.RayTracing": 0,                       # no HW RT on Apple Silicon
    }

    executor = unreal.MoviePipelinePIEExecutor()
    subsystem.render_queue_with_executor_instance(executor)
    unreal.log(f"Gate 0 render started for stage={stage} → {OUT_ROOT}/{stage}")
