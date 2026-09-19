# Gate 0 — Human fidelity spike

Spec: design doc §13.1. This folder is the working area. Nothing here depends on the world
engine, IR, or planner; the only pipeline artifact is `character/alice.yaml`.

```
character/alice.yaml     the input — authoritative character definition, three life stages
unreal/render_passes.py  MRQ render with RGB + depth + normals + motion vectors + object IDs
eval/viewer_protocol.md  blind viewer questions (Overall, Same person, Correct stage, Beautifier)
eval/scorecard.md        fill this in; the decision goes at the bottom
eval/extract_frames.sh   pull critical / face-closest frames from a render
eval/identity_distance.py  variant-separation check (face embeddings, conv vs. gen)
renders/<stage>/         EXR sequences from Unreal (git-ignored)
results/                 generative outputs, viewer answers, filled scorecard
```

## Prerequisites

| Need | Status | Who |
| --- | --- | --- |
| Unreal Engine 5.4+ (Apple Silicon native) via Epic Games Launcher | not installed | you |
| Epic account with Fab access (MetaHuman, kitchen, mocap) | ? | you |
| MetaHuman Creator (browser) + Quixel Bridge / Fab plugin in UE | after UE | you |
| A kitchen environment from Fab with a refrigerator that has (or can be given) a hinged door | ? | you |
| Mocap clips: walk, turn, open, reach/grasp, retract, close — Fab or Mixamo | ? | you |
| iPhone with Face ID + Live Link Face app (optional; fallback is hand-keyed blinks) | ? | you |
| Cloud GPU or hosted API for 2–3 video-to-video models with structural + identity conditioning | ? | you |
| `pip install insightface onnxruntime numpy opencv-python` for the eval script | ready | — |
| ffmpeg | installed | — |

This machine (M1 Max, 64 GB) handles the conventional half. The generative half runs on cloud.

## Week-by-week (two people; ~5–7 weeks)

**Week 1**
- A: Install UE. Build the three MetaHumans from `alice.yaml` in MetaHuman Creator — set the
  `shared` block first and lock it, then vary per stage. Export via Bridge. Record the Creator
  settings you used back into the yaml as comments.
- B: Shortlist 2–3 video-to-video models that accept depth/normal/pose conditioning AND
  reference-image identity conditioning. Get one running end to end on any test clip. Record
  cost per second of output.

**Week 2**
- A: Kitchen in, fridge door on a hinge, can placed. Mocap clips in, retargeted once to the
  MetaHuman skeleton. Rough Level Sequence for the young stage: walk → turn → open → grasp →
  retract → close, ~20 s.
- B: Conditioning pipeline: EXR layers → whatever the model wants. Identity-ref ingestion.

**Week 3**
- A: Contact IK at the three events (Control Rig or Full Body IK node). **Before enabling IK,
  measure the hand-to-handle miss per stage and write it in the scorecard** — that number is
  the contract's IK term, measured. Then enable IK; hand must land on all three stages. Old
  stage: add the 8° stoop as an additive spine offset; verify contact still lands.
- B: Eval scripts tested on any face video; viewer protocol dry-run with one person.

**Week 4**
- A: Camera: follow-from-behind, orbit to three-quarter through the grasp. Blinks, eye darts,
  one small expression at the grasp (Live Link Face or hand-keyed). `render_passes.py` for
  all three stages. mp4 of FinalImage for viewers. 8 identity stills per stage.
- B: Run each model on the young stage's native-window grasp clip first. Look at it. Fix
  conditioning before spending on 20 s.

**Week 5**
- B: All three stages × all models, native-window grasp clip then full 20 s. Log attempts,
  cost, manual fixes.
- A + B: Frame extraction; `identity_distance.py`; per-frame hand/face checks at the 5 contact
  + 3 face-closest frames.

**Week 6**
- Blind viewers, ≥ 5, per `viewer_protocol.md`. Fill `scorecard.md`. Write the decision.
- Update design doc §13.1 with what was actually measured and the outcome.

## Rules

- Same clips, same camera, same kitchen for all three stages. Do not age the motion.
- Judge the native-window grasp clip before the stitched 20 s. Report both.
- Measure the IK-off hand miss before turning IK on. It's the one number that tells you what
  the rig contract costs.
- Every attempt counts. A result that needed 12 tries is a 12-try result.
