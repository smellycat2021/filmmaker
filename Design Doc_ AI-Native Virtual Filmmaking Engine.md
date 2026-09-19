# Design Doc: AI-Native Virtual Filmmaking Engine

**Status:** Draft v0.2
**Target:** Small-team prototype
**Initial scope:** A 15–30-second cinematic sequence with persistent characters, environments, objects, and controllable cameras.

**Changes from v0.1:** Split the project into two independently testable hypotheses (Gate A: virtual production, Gate B: generative fidelity). Defined the production IR as the first deliverable. Replaced generalized motion synthesis with authored action clips against a frozen asset set. Replaced the custom camera optimizer and dependency graph with engine-native camera rigs and a versioned manifest. Rewrote the feasibility experiment with a two-camera fixture, an evaluation matrix, and pre-committed outcomes. Fixed the coordinate convention, added audio to non-goals, and cleaned up formatting.

---

The core idea is to treat a screenplay as a specification for a persistent virtual production, rather than as a collection of prompts for independent video clips.

The system constructs a reusable 3D world, executes character and object actions within it, plans camera movements and lighting, and converts the resulting performance into cinematic 2D footage through rendering and, optionally, generative refinement.

The key architectural principle is:

> The world engine determines what happens and where. The cinematography engine determines what the audience sees. The renderer determines how it looks.

## 1. Executive summary

### 1.1 Problem

Current prompt-to-video workflows can generate visually impressive short clips, but producing a coherent multi-shot narrative remains difficult.

Common failure modes include:

* Character appearance changing between shots.
* Objects disappearing, changing shape, or moving unexpectedly.
* Inconsistent room layouts and spatial relationships.
* Implausible hand-object contact and body movement.
* Camera motion that does not correspond to a coherent physical environment.
* Lighting, shadows, and exposure changing unexpectedly.
* Expensive regeneration when a director wants to change only one aspect of a shot.

The underlying problem is that independent video clips do not share an authoritative representation of the world or its evolving state.

### 1.2 Proposed solution

Build a virtual filmmaking engine with three distinct responsibilities:

| Layer | Responsibility |
| --- | --- |
| World simulation | Maintain characters, environments, objects, actions, and continuity. |
| Virtual cinematography | Plan and execute cameras, framing, lighting, and shot composition. |
| Visual synthesis | Render the performance as final footage — conventionally, or with generative refinement. |

A screenplay is compiled into a structured production plan. The system generates or retrieves persistent assets, executes actions in a shared 3D world, and renders the resulting performance through virtual cameras.

Conventional 3D rendering is a supported output mode with its own quality bar. Generative video is an optional refinement layer on top of it, never the authority for scene geometry or continuity.

### 1.3 Two hypotheses, tested independently

v0.1 bundled two claims into one plan. v0.2 separates them:

| Hypothesis | Gate | Question |
| --- | --- | --- |
| **H-A: Virtual production** | Gate A | Can we compile structured filmmaking instructions into a coherent, editable, multi-shot 3D production? |
| **H-B: Generative fidelity** | Gate B | Can a generative video model convert that production into photorealistic footage without losing identity, geometry, actions, or camera movement — across shots? |

Gate A is the core product and must pass on its own. Gate B is an independent risk: it can fail without invalidating the project, and it runs as soon as Gate A produces structural renders — not after the script compiler.

### 1.4 Intended users

Initially, the system targets creators producing short, scripted narrative sequences with a limited number of characters and locations.

The first version is a creator-assisted production tool, not a fully autonomous movie generator.

## 2. Goals and non-goals

### 2.1 Goals

| ID | Goal |
| --- | --- |
| G1 | Maintain persistent identities for characters, environments, and props across shots. |
| G2 | Represent a scene as an executable 3D world with semantic relationships. |
| G3 | Compile screenplay actions into a sequence of authored motion clips and object-state transitions. |
| G4 | Support controllable cameras, including continuous movement and event-based instructions. |
| G5 | Support physically coherent lighting and camera projection. |
| G6 | Generate structural rendering passes for downstream visual synthesis. |
| G7 | Allow independent editing of character performance, camera movement, and lighting. Appearance editing is independent for the 3D layers; under generative refinement, re-sampling may perturb unrelated regions, and this is a known limitation rather than a goal. |
| G8 | Detect continuity violations and expose failures for human correction. |

### 2.2 Non-goals for the MVP

The initial version will not attempt:

* Arbitrary-length films or unrestricted environments.
* Arbitrary object interactions or generalized grasp synthesis.
* Automatic character or environment generation, arbitrary imported assets, or cross-topology motion retargeting (between different rig families). Same-topology proportion adaptation within the canonical rig (§6.2) is in scope and engine-native. **The MVP asset set and rig versions are frozen** (§5.4).
* Fully automatic expressive acting.
* Dialogue, audio, lip-sync, or voice. The screenplay format may contain dialogue; the MVP ignores it.
* Guaranteed photorealism.
* Continuous generative shots longer than the selected video model's native window (§10.4).
* Training a foundational video model or building a custom 3D engine.

The MVP may require human approval of generated assets, screenplay interpretation, shot plans, and final output.

## 3. Core design principles

**3.1 One world, multiple views.** A location and its objects exist independently of the shots that depict them. Multiple cameras observe the same underlying scene.

**3.2 One canonical timeline, with support for takes.** The MVP uses a single continuous performance observed by all cameras. Later, filmmakers may want different performances for different angles, as conventional productions do; each take must still reference the same scene assets and declare an explicit continuity relationship to the canonical timeline.

**3.3 Separate intent from execution.** The LLM specifies actions such as `pick_up(cup_01)`. A deterministic motion layer converts them into executable trajectories and contact constraints.

**3.4 Persistent identity and state.** Every important character and object has a stable identifier. Actions update authoritative world state, not just visual appearance.

**3.5 Geometry where necessary, imagery where sufficient.** Interactive characters, props, surfaces, and nearby obstacles require 3D representations. Distant or noninteractive backgrounds may use 2D or 2.5D representations.

**3.6 Deterministic control before generative refinement.** A valid animation and conventional render must exist before optional photorealistic synthesis.

**3.7 Human-directed production.** Creators must be able to inspect and override the LLM's interpretation, action plan, camera path, and lighting.

**3.8 Reproducible execution.** Each output records the versions of its assets, world state, action timeline, camera settings, rendering configuration, and generation parameters.

**3.9 The IR is the contract.** The production intermediate representation (§5.3) is defined and hand-authored before any LLM produces it. If the hand-authored scene does not execute, adding an LLM will not fix it.

## 4. System architecture

```
Screenplay + Creative Direction
  narrative, characters, locations, actions, style
        │
        ▼
Script Compiler / Production Planner          ← built AFTER Gate A; emits the IR
  structured scene specs, asset requirements, action plans
        │
        ▼
Production IR  ──────────────────────────────── the contract (§5.3)
        │
        ├──► Asset Registry
        │      characters, locations, props, rigs, appearance references
        ├──► Action Library
        │      authored motion clips, interaction contracts
        ▼
Persistent World Engine
  scene graph + semantic graph + authoritative state + timeline
        │
        ▼
Motion Runtime
  clip sequencing, blending, attachment, limited IK, collision checks
        │
        ▼
Cinematography Engine
  engine-native camera rigs, authored paths, event sync, lighting
        │
        ▼
3D Renderer  ──────────────────────────────────  supported output (Gate A)
  RGB, depth, normals, segmentation, motion vectors
        │
        ▼
Generative Refinement (optional)  ─────────────  independent risk (Gate B)
  photorealistic appearance and temporal synthesis
        │
        ▼
Verification → Editing → Final Film
```

The authoritative outputs of the system are the asset definitions, world-state timeline, animation, and camera specifications. Rendered video — conventional or generative — is a derived artifact.

## 5. Production IR and preproduction

### 5.1 Input

The compiler accepts a screenplay containing scene descriptions, characters, dialogue, actions, and optional cinematography instructions.

Example:

> Alice enters the house, walks to the kitchen, opens the refrigerator, and grabs a can of soda. The camera follows her from behind, then moves to her right as she opens the refrigerator.

### 5.2 Compiler responsibilities

The compiler extracts the cast, locations, props, actions, temporal dependencies, and camera requirements.

It must distinguish between explicit screenplay facts and inferred production decisions. The screenplay explicitly requires a refrigerator and a soda can, but it may not specify which hand Alice uses or where the refrigerator is positioned. The compiler can propose those details, but they must become stable decisions once approved.

The compiler is built **after** Gate A passes. Until then, the IR is hand-authored.

### 5.3 Intermediate representation

The IR is a typed, versioned, schema-validated representation of a production. It is the first engineering deliverable of the project, not a byproduct of the compiler.

It contains:

* Asset references (characters, locations, props) by stable ID and version. A character reference names its `skeleton_id` (canonical rig, §6.2), its `rig_instance_id` (that character's proportion parameters), and its face rig separately from its body mesh.
* Action clip references tagged with the `skeleton_id` they were authored against.
* Scene definitions: location, cast, initial world state.
* An action timeline: ordered semantic actions with dependencies and event markers.
* Shot definitions: camera, lens, movement, and event-synchronized instructions.
* Lighting setup.
* Unresolved decisions and validation errors (missing prop, unsupported action, character entering a room with no doorway).

The manifest (§11.1), verification (§12), the review UI, and the compiler all key off this schema. Defining it in month 4 would force a retrofit of everything built in months 2–3.

**Coordinate convention (decided):** the IR uses the host engine's native convention. For Unreal Engine that is Z-up, left-handed, centimeters, with rotations as quaternions. Any asset prepared in Blender (Z-up, right-handed, meters) is converted on import, and the converted asset is what gets versioned.

### 5.4 Asset preproduction and the MVP asset freeze

The asset registry stores persistent character identities, body rigs, facial controls, wardrobes, locations, furniture, and interactive props.

For the MVP the asset set is **frozen**:

* One canonical adult-human rig (§6.2) and one rig instance (Alice) with fixed proportions, one face rig, and one wardrobe.
* One house environment with connected entry and kitchen.
* One refrigerator with a hinged door and known handle and interior grasp points.
* One soda can.

Authored motion clips (§7.2) are built against exactly these assets. No automatic character generation, no arbitrary imported refrigerator models, no cross-rig retargeting. This removes asset generation, rig compatibility, and motion transfer as variables from both gates; they are re-introduced only after the architecture is validated.

## 6. World model

The world model is the central source of truth. It consists of four related structures:

| Structure | Purpose |
| --- | --- |
| Scene graph | Spatial hierarchy, geometry, transforms, and parent-child relationships. |
| Semantic graph | Object types, affordances, and relationships such as `supports`, `contains`, and `connects_to`. |
| World state | Current locations, ownership, articulation states, and other mutable properties. |
| Event timeline | Ordered actions and state transitions, including their timing and dependencies. |

### 6.1 Object representation

Every interactive object requires a stable identity and sufficient geometry to support its intended interactions. A refrigerator is not merely a rectangular mesh. It has a door with a hinge, a handle, an interior storage volume, and designated grasp and placement points.

```json
{
  "id": "fridge_01",
  "type": "refrigerator",
  "parent": "kitchen_01",
  "transform": {
    "position_cm": [420.0, 150.0, 0.0],
    "rotation_quat": [0, 0, 0, 1]
  },
  "articulations": {
    "door": {
      "type": "hinge",
      "angle_degrees": 0,
      "range_degrees": [0, 110]
    }
  },
  "affordances": ["open", "close", "retrieve_object"],
  "grasp_points": {
    "handle": [412.0, 118.0, 105.0]
  },
  "contents": ["soda_can_01"]
}
```

### 6.2 Character representation

A character asset includes a persistent identity, a body rig instance, surface geometry, a face rig, clothing, and appearance references.

The rig should represent the degrees of freedom needed for supported actions rather than attempting to animate every anatomical bone independently. Hands, wrists, shoulders, spine, neck, and facial controls deserve particular attention because they strongly affect close-up interactions and acting.

#### Rig contract

Characters do not each get their own skeleton, and they do not all share one identically-proportioned skeleton. The design is a **shared canonical rig definition, instantiated and parameterized per character**:

```
Character body rig = Canonical Rig + Character Proportions + Character-Specific Constraints
```

* **Canonical rig** (`skeleton_id`): one shared joint hierarchy, bone naming, joint orientations, joint limits, and a fixed bind pose (A-pose). For the MVP this is the engine's standard adult-human skeleton (on Unreal, the MetaHuman/Mannequin skeleton).
* **Rig instance** (`rig_instance_id`): per-character bone lengths, shoulder and hip width, hand size, neck length, and similar anatomical parameters within plausible ranges. These are set independently, not by uniform scale — a skeleton multiplied by 0.9 still looks like the same person shrunk. The bind pose is **not** per-character; keeping it canonical is what makes proportion adaptation trivial.
* **Face rig**: per-character (blendshapes or a face control rig), stored as a separate asset from the body rig instance so the body contract stays clean.

All motion clips (§7.2) are authored against the canonical rig. Playing a clip on a character means two things:

1. **Same-topology adaptation** for locomotion and gesture: the clip's joint angles are applied to the character's instance; the engine handles differing bone lengths natively. This is not the cross-topology retargeting excluded in §2.2.
2. **IK pinning at contact events** for anything that touches an object: proportion adaptation preserves *pose*, not *end-effector position*. A character with 8% longer arms plays `reach` with the hand 8% past the fridge handle. The limited IK in §7.2 closes that gap at `reach_target`, `grip_established`, and `release` events. This IK is the mechanism that makes per-character proportions work at all; it is not optional.

Non-human or non-adult characters (child, infant, quadruped) need separate canonical rig families with their own clips, because an adult rig shrunk to toddler size has the wrong balance, joint ranges, and stride mechanics. Rig families are post-MVP.

**MVP:** one canonical adult-human rig, one instance (Alice). Adding a second instance with different proportions (Bob) is the first post-Gate-A extension and a direct test of this contract: if Alice's clips plus IK pinning still land Bob's hand on the handle and the can, the rig contract holds.

### 6.3 World-state transitions

An action such as retrieving a soda can changes the world state.

```
Before:
  fridge.door = closed
  soda.location = fridge.interior
  soda.holder = none

After opening:
  fridge.door = open

After grasping:
  soda.location = attached_to(alice.right_hand)
  soda.holder = alice
```

The animation and state transition must agree. The can must not become attached to Alice's hand before physical contact occurs.

State changes occur at defined action events, such as `grip_established`, rather than at arbitrary timestamps.

### 6.4 Continuity

All shots reference the same world timeline. A shot may observe only a portion of an action, but it cannot independently reset the world.

If Alice removes the soda from the refrigerator, subsequent shots must reflect that state unless an explicit event puts the soda back.

## 7. Action and motion engine

### 7.1 Hierarchical action model

Actions are represented at three levels:

| Level | Example |
| --- | --- |
| Semantic action | Retrieve soda from refrigerator |
| Motion composition | Approach → Open → Reach → Grasp → Retract |
| Executed motion | Authored clips sequenced and blended; attachment events; limited IK correction; collision checks |

The LLM selects semantic actions. The motion runtime executes them.

### 7.2 Authored motion clips (MVP)

v0.1 described parameterized primitives — a `grasp` that adapts to arbitrary grip configurations and target geometry. That is a research problem and is out of scope.

For the MVP, the action library is a set of **authored clips** (mocap or hand-keyed) for the frozen asset set:

walk, turn, reach, grasp, carry, open, close, release

Each clip is authored against the known character proportions, the fixed refrigerator, and the known handle and can positions. The planner sequences and blends clips; it does not synthesize them.

The runtime still needs a small amount of correction machinery: limited IK to close alignment errors at contact events (the IK pinning described in the rig contract, §6.2), and attachment handling at `grip_established` / `release` events. Generalized grasp synthesis, arbitrary object geometry, and physically robust manipulation are post-MVP.

### 7.3 Interaction contracts

Every interactive action declares preconditions, effects, and validation rules.

```
Action: retrieve_object(actor, container, object)

Preconditions:
  actor can reach container
  object is inside container
  container is open

Effects:
  object is attached to actor's hand
  object is no longer stored inside container

Validation:
  hand reaches object
  grip contact is established
  object does not intersect container during extraction
```

The planner must either satisfy the preconditions or insert prerequisite actions. If the refrigerator is closed, it opens the door before retrieving the can.

### 7.4 Motion execution

A clip is a starting point, not proof that the resulting interaction is valid. The execution layer checks collisions, reachability, support, and hand-object contact at critical frames.

The MVP prioritizes reliable execution over breadth of vocabulary.

## 8. Virtual cinematography engine

### 8.1 Scene versus shot

A scene defines a location, cast, world state, and action timeline. A shot defines a camera observing some interval of that timeline. Multiple shots may observe the same performance without duplicating or independently generating the underlying actions.

### 8.2 Camera model

A camera asset includes its world transform, projection model, sensor dimensions, focal length, focus distance, aperture, exposure parameters, and movement trajectory.

The fundamental projection is the standard pinhole model:

```
p̃ ~ K [R | t] P_w
```

where `K` is the intrinsic matrix, `[R | t]` the extrinsic pose, and `P_w` a world-space point. The 3D renderer then resolves visibility, surfaces, shading, and lighting to produce 2D frames.

### 8.3 Camera operator

The camera operator translates high-level cinematic instructions into executable trajectories.

Supported MVP commands: `static`, `follow`, `dolly`, `orbit`. (`track`, `pan`, `tilt` are deferred.)

```json
{
  "camera_id": "camera_a",
  "shot_id": "shot_03",
  "lens_mm": 35,
  "movement": {
    "type": "follow",
    "subject": "alice",
    "relative_position": "behind",
    "distance_cm": 200
  },
  "event_instructions": [
    {
      "event": "fridge_door_opening",
      "operation": "orbit",
      "direction": "right",
      "degrees": 45
    }
  ]
}
```

### 8.4 Camera implementation (MVP)

v0.1 proposed a custom constraint optimizer over framing, occlusion, collision, and smoothness losses. That is removed from the MVP.

Instead:

* **Engine-native camera rigs** (Unreal cine camera, spring arm) for `follow` and `orbit`.
* **Authored paths** for `dolly` and for any move that must route through the house — a spring arm avoids some collisions but does not find a usable route through a doorway or preserve composition while doing so.
* **Collision and framing detection, not solving.** The system flags wall penetration and loss of subject; a human fixes the path. The director can explicitly authorize an impossible move.

A planner that solves for framing and route is a post-MVP item, justified only if authored paths become the iteration bottleneck.

### 8.5 Event synchronization

Camera instructions may depend on action events instead of fixed timestamps. The camera begins orbiting when the refrigerator door starts opening. If the performance is retimed, the camera plan adapts without the director manually updating every keyframe.

## 9. Lighting and environment rendering

Lighting is part of the persistent production setup. Light sources have positions, orientations, intensities, colors, shapes, and animation parameters. Environment lighting may include sunlight, windows, practical lights, and ambient illumination.

The system supports lighting presets while preserving the ability to adjust individual sources. A lighting setup may be shared across several shots, while exposure and camera-specific optical settings vary.

The renderer outputs a conventional RGB pass and, where supported, structural passes: depth, normals, object segmentation, motion vectors, and lighting information.

**The conventional RGB render is a product output, not a preview.** It has its own quality bar (Gate A, §13) and must be exportable as a finished sequence regardless of whether generative refinement is used.

## 10. Generative video rendering

### 10.1 Purpose

The generative renderer converts the virtual production's structural output into the desired final visual style.

Inputs may include RGB and structural passes, persistent appearance references, camera and lighting metadata, temporal context from neighboring frames, and style instructions. Outputs are video frames plus generation metadata.

### 10.2 Authority boundary

The renderer is responsible for visual synthesis, not deciding what happened in the scene. It should preserve object identity, spatial relationships, camera movement, and action timing.

This cannot be guaranteed by defining an interface. It must be demonstrated experimentally with the actual model and conditioning mechanism — that is Gate B (§13.3).

### 10.3 Conventional rendering is the baseline, not a fallback

The conventional 3D render (§9) is always available, always exportable, and is the reference against which generative output is measured. If Gate B fails, the product continues on the conventional path.

### 10.4 Long sequences

The engine maintains one continuous world and action timeline even if the video model processes shorter clips.

The MVP benchmark uses short shots within the model's native window. A continuous 20–30-second generative tracking shot is a **separate, later experiment**; overlapping-window generation and boundary reconciliation are candidate approaches, not assumed solutions. The MVP does not assume that independently generating adjacent clips produces seamless motion.

## 11. Execution workflow

1. **Author or compile the IR.** Hand-authored for the MVP benchmark; compiler-generated after Gate A. Present ambiguous decisions for review.
2. **Prepare assets.** Frozen set for the MVP. Validate rigs and interaction affordances.
3. **Build world.** Instantiate assets, establish spatial and semantic relationships, initialize authoritative state.
4. **Plan and execute actions.** Resolve semantic actions into authored clips, animate, record state transitions.
5. **Plan cinematography.** Select shots, cameras, lenses, movement, lighting, focus. Synchronize camera instructions with action events.
6. **Render.** Produce conventional RGB and structural passes. Optionally apply generative refinement.
7. **Verify and edit.** Inspect continuity, geometry, interaction correctness, camera adherence, and visual quality.

### 11.1 Production manifest and regeneration

Each output records a manifest: screenplay version, asset versions, IR version, action-plan version, scene-state version, camera configuration, renderer settings, model version, and generation seed where supported. Every entry is content-hashed.

**MVP regeneration policy: full re-render.** v0.1 proposed a dependency graph with selective invalidation. That is deferred. The manifest makes it possible to tell what changed; it does not yet drive partial regeneration.

Re-render cost is not assumed to be small. It depends on resolution, renderer, hardware, and whether generative inference is included — and generative inference is where cost will bite first. The MVP **measures** per-shot cost for both paths (see Gate B, §13.3). Selective invalidation is built when measured cost justifies it, and the manifest's hashes are what will drive it when that happens.

## 12. Verification and quality control

Verification is split into deterministic checks and perceptual checks.

| Category | Example validation |
| --- | --- |
| Asset integrity | Referenced characters and props exist and have compatible rigs. |
| World state | Object locations and ownership follow valid transitions. |
| Motion | Character reaches target; joint limits and collisions are respected. |
| Interaction | Hand-object contact and attachment timing are consistent. |
| Camera | Subject is visible; camera follows the planned trajectory; no unauthorized wall penetration. |
| Rendering | Structural passes are synchronized and contain valid data. |
| Generated video | Character identity, object identity, geometry, and camera movement are preserved. |
| Continuity | Adjacent shots agree on relevant state and appearance. |

The system distinguishes a verified 3D simulation (Gate A) from a verified final video (Gate B). Passing collision checks in 3D does not prove that a generative renderer preserved those contacts.

The MVP exposes side-by-side conventional and generative playback so reviewers can identify which stage introduced a failure.

## 13. MVP definition and gates

### 13.1 Demonstration sequence

> Alice approaches a house, opens the front door, enters, walks to the kitchen, opens the refrigerator, retrieves a soda can, and closes the refrigerator.

The sequence must support both a continuous tracking-camera plan and an edited multi-shot version of the same performance.

| Scope | MVP |
| --- | --- |
| Characters | 1 (Alice), frozen rig |
| Locations | 1 house: connected entry and kitchen |
| Interactive props | Front door, refrigerator, soda can |
| Actions | walk, turn, reach, grasp, carry, open, close, release — authored clips |
| Camera modes | static, follow, dolly, orbit |

### 13.2 Gate A: Virtual production (core product)

Gate A passes if the system, from a hand-authored IR, can:

1. Execute the entire action sequence in a persistent 3D world without invalid object-state transitions (verified by the §12 world-state and interaction checks).
2. Produce a camera trajectory that follows Alice through the doorway and kitchen with no unauthorized collisions and the subject in frame throughout.
3. Render the same performance from a second, different camera plan with the world state and animation unchanged (byte-identical action timeline and state log).
4. Produce structural passes with consistent geometry and object identities across both camera plans.
5. Allow a reviewer to modify a camera instruction and re-render without touching character, environment, or action assets.
6. Export a conventional RGB sequence for both camera plans that a reviewer accepts as a coherent scene.

Gate A must pass regardless of Gate B's outcome. Passing Gate A is a meaningful product result on its own.

### 13.3 Gate B: Generative fidelity (independent risk)

Gate B runs **as soon as Gate A produces structural renders for the two-camera fixture**, in parallel with compiler work. It does not wait for the script compiler.

**Fixture.** The frozen kitchen, Alice, refrigerator, and can. Alice opens the refrigerator and retrieves the can. The same performance is rendered from two camera angles (A: follow-from-behind orbiting right on `fridge_door_opening`; B: static three-quarter from the kitchen side). Both are within the video model's native clip length.

**Generation modes.** Run both:

* **Cold:** each shot generated independently from its own structural passes and shared appearance references.
* **Chained:** shot B generated with shot A's output frames as additional reference.

Which mode holds identity determines whether cross-shot consistency is an asset-conditioning problem or a sequential-generation problem; these lead to different pipelines.

**Evaluation matrix.** Thresholds are initial and are refined with the measurement protocol before the first run — but they are written down now so results are judged against something.

| Property | Measurement | Initial threshold |
| --- | --- | --- |
| Character identity | Face/body embedding similarity vs. reference, within each clip and across A↔B; reviewer check for wardrobe | Cross-shot similarity ≥ within-shot similarity minus a small margin; no reviewer-flagged identity break |
| Environment | Refrigerator and kitchen layout match structural render on designated frames | No reviewer-flagged geometry change; segmentation IoU vs. structural pass ≥ 0.85 on designated frames |
| Camera | Estimated camera pose from output vs. planned trajectory | Trajectory shape preserved; no direction reversal or lost subject |
| Door articulation | Door edge tracks projected hinge arc | Door opens around intended hinge; no reviewer-flagged shape change |
| Hand contact | Hand–can projected offset on 5 designated critical frames (reach, grip, lift, extract, carry) | ≤ 3 cm equivalent in projected space; no reviewer-flagged detachment |
| Object continuity | Can tracked through clip | Same object throughout; follows intended trajectory |
| Cross-shot continuity | State at the cut point (door angle, can location, hand pose) agrees between A and B | Reviewer confirms agreement at cut |

**Also record:** wall-clock runtime, inference cost, number of attempts before an acceptable result, and manual correction time. A result that works only after extensive selection demonstrates possibility, not an economical workflow.

**Pre-committed outcomes.**

| # | Result | Decision |
| --- | --- | --- |
| 1 | All checks pass in at least one mode | Adopt generative refinement as a supported rendering mode. |
| 2 | Appearance passes; contact fails | Run a follow-up mini-experiment on masked/regional refinement (generative for environment and materials, conventional for the interaction). Regional refinement is itself untested and commonly seams at the mask boundary; it is not assumed to work. |
| 3 | Single shot passes; cross-shot identity fails in both modes | Investigate reference conditioning and identity preservation before claiming multi-shot support. Do not build multi-shot generative features on the unvalidated assumption. |
| 4 | Camera or geometry fails | Change conditioning approach or model. Do not build the larger generative workflow on the failed assumption. |
| 5 | Conventional passes (Gate A); generative fails | Continue the virtual-production product on the conventional path. Defer generative refinement; revisit when models or conditioning improve. |

## 14. Technical strategy and implementation choices

### 14.1 Build versus buy

Integrate an existing 3D engine rather than implement rendering, skeletal animation, physics, and camera systems from first principles.

The practical candidate is Unreal Engine, with its cinematic sequencing, animation, camera rigs, and rendering-pass support. Blender may be used for asset preparation and offline rendering, with assets converted to the engine convention on import (§5.3).

Engine selection is based on automation APIs, asset compatibility, rendering-pass support, licensing, deployment constraints, and developer familiarity.

The team owns the IR, screenplay compiler, orchestration, semantic world model, action sequencing, continuity tracking, manifest, and verification logic.

### 14.2 Suggested subsystem boundaries

```
production/
  ir/               ← first deliverable
  screenplay/       ← after Gate A
  asset_registry/
  world_model/
  action_planner/
  motion_runtime/
  cinematography/
  rendering/
  refinement/
  verification/
  editor/
```

The world engine and rendering engine communicate through explicit asset references, scene-state snapshots, and timeline definitions.

The LLM never mutates the rendering engine directly. Its output passes through IR schema validation and a deterministic execution layer.

### 14.3 Reproducibility

See §11.1. The manifest is the reproducibility record.

## 15. Key risks and mitigation

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Video model ignores structural constraints | Final footage contradicts the simulation | Gate B with pre-committed outcomes; conventional path is a product, not a fallback. |
| Cross-shot identity drifts under generation | Multi-shot continuity breaks | Two-camera fixture in Gate B; cold vs. chained modes; identity checks. |
| Hand-object interactions fail in 3D | Common actions look implausible | Frozen assets, authored clips, limited IK, contact validation at critical frames. |
| Asset / rig incompatibility | Clips authored for one rig don't transfer | Asset freeze for MVP; no retargeting requirement. |
| Camera paths invalid | Camera intersects geometry or loses the subject | Engine-native rigs, authored paths, collision detection with human fix. |
| Script interpretation ambiguous | Incorrect or inconsistent production decisions | Typed IR, unresolved-decision tracking, human review; compiler built only after Gate A. |
| Regeneration cost excessive | Slow iteration and poor economics | Measure first (Gate B cost recording); build selective invalidation on evidence. |
| Long generative shots | Seams at clip boundaries | Deferred to a separate experiment; MVP uses short shots. |
| System complexity overwhelms the team | Integration stalls before a useful demo | Two gates, one benchmark, frozen assets, engine-native components. |

## 16. Development roadmap

Planning estimate for three to four experienced contributors; not a delivery commitment.

| Phase | Timeline | Deliverable |
| --- | --- | --- |
| IR + world foundation | Months 1–2 | IR schema; hand-authored benchmark IR; frozen assets; persistent world; action timeline; state transitions; authored clips |
| Cinematography + structural renders | Months 2–3 | Engine-native camera rigs; event sync; lighting; two-camera fixture; conventional RGB + structural passes |
| **Gate A review** | End of month 3 | §13.2 criteria |
| Gate B experiment | Months 3–4, **in parallel with the row below** | §13.3 fixture, both modes, evaluation matrix, cost record, decision |
| Script compiler | Months 4–5 | LLM → IR; validated action plans; review workflow |
| End-to-end prototype | Month 6 | Complete benchmark from screenplay; alternate camera edit; verification report; generative mode if Gate B outcome 1 or 2 |

Gate A is the first decision point: if a hand-authored scene cannot execute coherently, the compiler is not started. Gate B is the second and is independent: its outcome selects which rendering modes the month-6 prototype ships with.

## 17. Open design questions

To resolve through prototypes rather than upfront specification.

| Question | Why it matters |
| --- | --- |
| How much 3D detail does the generative renderer need? | Determines asset cost and whether structural passes give sufficient guidance. Partly answered by Gate B. |
| What conditioning interface does the video model actually support? | Determines whether camera, geometry, and motion constraints can be enforced. Answered by Gate B. |
| Cold vs. chained cross-shot generation | Determines the multi-shot pipeline shape. Answered by Gate B. |
| When do takes (§3.2) need to enter the world model? | Post-MVP; depends on whether continuous performance limits acting quality. |
| How much motion should be procedural versus learned, post-MVP? | Determines coverage, realism, and debugging complexity once the frozen asset set is lifted. |
| What is the minimum acceptable level of human intervention? | Defines the boundary between an assisted tool and an autonomous system. |
| What constitutes a commercially successful conventional render? | Gate A defines coherence, not market quality. |

## 18. Immediate next step

Build the IR schema and hand-author the benchmark scene in it. Stand up the frozen asset set in the engine. Author the eight clips. Get Alice through the door and the can out of the refrigerator from two cameras, conventionally rendered, with structural passes.

That is Gate A. The moment it produces structural renders for the two-camera fixture, start Gate B.

### Final design thesis

Build a persistent, executable virtual production rather than a collection of independently generated clips.

The screenplay defines intent. The IR is the contract. The world model establishes reality. The motion runtime executes actions. The cinematography engine selects the audience's viewpoint. The renderer produces the image — conventionally by default, generatively when it can be shown to preserve the production. The verifier checks whether the final footage remains faithful.

The near-term goal is not autonomous feature-film generation. It is a controllable, reusable production pipeline that can make one short, coherent scene — and then make it again with a different camera, lighting setup, or visual treatment without starting from scratch.
