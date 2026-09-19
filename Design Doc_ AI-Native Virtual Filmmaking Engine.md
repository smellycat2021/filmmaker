# **Design Doc: AI-Native Virtual Filmmaking Engine**

Status: Draft v0.1 Target: Small-team prototype Initial scope: A 15–30-second cinematic sequence with persistent characters, environments, objects, and controllable cameras.

The core idea is to treat a screenplay as a specification for a persistent virtual production, rather than as a collection of prompts for independent video clips.

The system constructs a reusable 3D world, executes character and object actions within it, plans camera movements and lighting, and converts the resulting performance into cinematic 2D footage through rendering and generative refinement.

The key architectural principle is:

> The world engine determines what happens and where. The cinematography engine determines what the audience sees. The generative renderer determines how it looks.

Below is a design document structured around the product thesis, architecture, data models, execution pipeline, technical risks, and a realistic MVP.

## **1\. Executive summary**

### **1.1 Problem**

Current prompt-to-video workflows can generate visually impressive short clips, but producing a coherent multi-shot narrative remains difficult.

Common failure modes include:

* Character appearance changing between shots.  
* Objects disappearing, changing shape, or moving unexpectedly.  
* Inconsistent room layouts and spatial relationships.  
* Implausible hand-object contact and body movement.  
* Camera motion that does not correspond to a coherent physical environment.  
* Lighting, shadows, and exposure changing unexpectedly.  
* Expensive regeneration when a director wants to change only one aspect of a shot.

The underlying problem is that independent video clips do not necessarily share an authoritative representation of the world or its evolving state.

### **1.2 Proposed solution**

Build a virtual filmmaking engine with three distinct responsibilities:

|  
Layer

|

Responsibility

|  
| \--- | \--- |  
|

World simulation

|

Maintain characters, environments, objects, actions, and continuity.

|  
|

Virtual cinematography

|

Plan and execute cameras, framing, lighting, and shot composition.

|  
|

Visual synthesis

|

Convert structural renders into visually compelling final footage.

|

A screenplay is compiled into a structured production plan. The system generates or retrieves persistent assets, executes actions in a shared 3D world, and renders the resulting performance through virtual cameras.

Generative video is an optional visual-refinement layer rather than the authority for scene geometry or continuity.

### **1.3 Product hypothesis**

Separating world simulation from visual synthesis will improve controllability, consistency, and editability compared with independently prompting every shot.

This is a hypothesis to validate, not an established result. The first prototype must demonstrate that the chosen generative renderer can preserve geometry, character identity, camera movement, and object interactions sufficiently well.

### **1.4 Intended users**

Initially, the system targets creators producing short, scripted narrative sequences with a limited number of characters and locations.

The first version is a creator-assisted production tool, not a fully autonomous movie generator.

## **2\. Goals and non-goals**

### **2.1 Goals**

|  
ID

|

Goal

|  
| \--- | \--- |  
|

G1

|

Maintain persistent identities for characters, environments, and props across shots.

|  
|

G2

|

Represent a scene as an executable 3D world with semantic relationships.

|  
|

G3

|

Compile screenplay actions into reusable motion primitives and object-state transitions.

|  
|

G4

|

Support controllable cameras, including continuous movement and event-based instructions.

|  
|

G5

|

Support physically coherent lighting and camera projection.

|  
|

G6

|

Generate structural rendering passes for downstream visual synthesis.

|  
|

G7

|

Allow independent editing of character performance, camera movement, lighting, and appearance.

|  
|

G8

|

Detect continuity violations and expose failures for human correction.

|

### **2.2 Non-goals for the MVP**

The initial version will not attempt arbitrary-length films, unrestricted environments, arbitrary object interactions, fully automatic expressive acting, or guaranteed photorealism.

It will not train a foundational video model or build a custom 3D engine from scratch.

The MVP may require human approval of generated assets, screenplay interpretation, shot plans, and final output.

## **3\. Core design principles**

3.1 One world, multiple views. A location and its objects exist independently of the shots that depict them. Multiple cameras observe the same underlying scene.

3.2 Separate intent from execution. The LLM specifies actions such as `pick_up(cup_01)`. A motion engine converts them into executable trajectories and contact constraints.

3.3 Persistent identity and state. Every important character and object has a stable identifier. Actions update authoritative world state, not just visual appearance.

3.4 Geometry where necessary, imagery where sufficient. Interactive characters, props, surfaces, and nearby obstacles require 3D representations. Distant or noninteractive backgrounds may use 2D or 2.5D representations.

3.5 Deterministic control before generative refinement. A valid animation and structural render must exist before optional photorealistic synthesis.

3.6 Human-directed production. Creators must be able to inspect and override the LLM's interpretation, action plan, camera path, and lighting.

3.7 Reproducible execution. Each output records the versions of its assets, world state, action timeline, camera settings, rendering configuration, and generation parameters.

## **4\. System architecture**

# **High-level architecture**

Screenplay \+ Creative Direction

Narrative, characters, locations, actions, style

Script Compiler / Production Planner

Structured scene specifications, asset requirements, action plans

Asset Registry

Characters, locations, props, rigs, appearance references

Action Library

Motion primitives, interaction affordances, constraints

Persistent World Engine

Scene graph \+ interaction graph \+ authoritative state \+ timeline

Motion Engine

Characters, props, IK, contacts, collisions

Cinematography Engine

Camera paths, lenses, framing, lighting

3D Renderer

RGB, depth, normals, segmentation, motion vectors

Generative Refinement

Photorealistic appearance and temporal synthesis

Verification → Editing → Final Film

The authoritative outputs of the system are the asset definitions, world-state timeline, animation, and camera specifications. Generated video is a derived artifact.

This makes it possible to regenerate an individual shot without rebuilding the entire production.

## **5\. Script compiler and preproduction**

### **5.1 Input**

The compiler accepts a screenplay containing scene descriptions, characters, dialogue, actions, and optional cinematography instructions.

Example:

> Alice enters the house, walks to the kitchen, opens the refrigerator, and grabs a can of soda. The camera follows her from behind, then moves to her right as she opens the refrigerator.

### **5.2 Compiler responsibilities**

The compiler extracts the cast, locations, props, actions, temporal dependencies, and camera requirements.

It must distinguish between explicit screenplay facts and inferred production decisions.

For example, the screenplay explicitly requires a refrigerator and a soda can, but it may not specify which hand Alice uses or where the refrigerator is positioned. The compiler can propose those details, but they must become stable decisions once approved.

### **5.3 Intermediate representation**

The screenplay is compiled into a typed production representation rather than passed directly to the renderer as free-form text.

A scene specification references existing assets where possible and creates new asset requirements where necessary.

The compiler also produces unresolved decisions and validation errors.

Examples include a missing prop, an action unsupported by the current motion library, or a character attempting to enter a room that has no connecting doorway.

### **5.4 Asset preproduction**

The asset registry stores persistent character identities, body rigs, facial controls, wardrobes, voice references, locations, furniture, and interactive props.

Assets may be generated, imported, or selected from a library.

Character and location appearance references should be created before final shot generation. However, asset development may proceed incrementally as the production reveals additional requirements.

## **6\. World model**

The world model is the central source of truth.

It consists of four related structures:

|  
Structure

|

Purpose

|  
| \--- | \--- |  
|

Scene graph

|

Spatial hierarchy, geometry, transforms, and parent-child relationships.

|  
|

Semantic graph

|

Object types, affordances, and relationships such as `supports`, `contains`, and `connects_to`.

|  
|

World state

|

Current locations, ownership, articulation states, and other mutable properties.

|  
|

Event timeline

|

Ordered actions and state transitions, including their timing and dependencies.

|

### **6.1 Object representation**

Every interactive object requires a stable identity and sufficient geometry to support its intended interactions.

A refrigerator, for example, is not merely a rectangular mesh. It has a door with a hinge, a handle, an interior storage volume, and designated grasp and placement points.

JSON

{  
  "id": "fridge\_01",  
  "type": "refrigerator",  
  "parent": "kitchen\_01",  
  "transform": {  
    "position": \[4.2, 0.0, 1.5\],  
    "rotation": \[0, 0, 0\]  
  },  
  "articulations": {  
    "door": {  
      "type": "hinge",  
      "angle\_degrees": 0,  
      "range\_degrees": \[0, 110\]  
    }  
  },  
  "affordances": \[  
    "open",  
    "close",  
    "retrieve\_object"  
  \],  
  "contents": \["soda\_can\_01"\]  
}

Coordinates are illustrative. The production schema must define one consistent coordinate system, unit convention, and rotation representation.

### **6.2 Character representation**

A character asset includes a persistent identity, skeletal rig, surface geometry, facial controls, clothing, and appearance references.

The rig should represent the degrees of freedom needed for supported actions rather than attempting to animate all 206 anatomical bones independently.

Hands, wrists, shoulders, spine, neck, and facial controls deserve particular attention because they strongly affect close-up interactions and acting.

### **6.3 World-state transitions**

An action such as retrieving a soda can changes the world state.

Before:  
  fridge.door \= closed  
  soda.location \= fridge.interior  
  soda.holder \= none

After opening:  
  fridge.door \= open

After grasping:  
  soda.location \= attached\_to(alice.right\_hand)  
  soda.holder \= alice

The animation and state transition must agree. The can should not become attached to Alice's hand before physical contact occurs.

For reliability, state changes should occur at defined action events, such as `grip_established`, rather than at arbitrary timestamps.

### **6.4 Continuity**

All shots reference the same world timeline.

A shot may observe only a portion of an action, but it cannot independently reset the world.

If Alice removes the soda from the refrigerator, subsequent shots must reflect that state unless an explicit event puts the soda back.

## **7\. Action and motion engine**

### **7.1 Hierarchical action model**

Actions are represented at three levels:

Semantic action

Retrieve soda from refrigerator

Motion composition

Approach → Open → Reach → Grasp → Retract

Joint and object trajectories

IK, balance, contact, articulation, collision avoidance

The LLM selects semantic actions. The motion engine generates the trajectories needed to execute them.

### **7.2 Reusable motion primitives**

The initial library should cover a small set of common behaviors: walking, turning, reaching, grasping, carrying, opening, closing, releasing, and sitting.

Each primitive should be parameterized by target, duration, speed, acting style, and relevant physical constraints.

A `grasp` primitive, for example, must support different grip configurations and target geometry rather than replaying one fixed animation.

### **7.3 Interaction contracts**

Every interactive action should declare preconditions, effects, and validation rules.

For example:

Action: retrieve\_object(actor, container, object)

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

The planner must either satisfy the preconditions or insert prerequisite actions. If the refrigerator is closed, it must open the door before retrieving the can.

### **7.4 Motion execution**

Motion generation can combine existing animation clips, retargeting, inverse kinematics, procedural motion, and learned motion models.

A motion clip is a starting point, not proof that the resulting interaction is valid.

The execution layer must check collisions, reachability, support, balance, and hand-object contact where applicable.

The MVP should prioritize reliable execution over the breadth of its action vocabulary.

## **8\. Virtual cinematography engine**

This subsystem turns the shared 3D performance into a film.

### **8.1 Scene versus shot**

A scene defines a location, cast, world state, and action timeline.

A shot defines a camera observing some interval of that timeline.

Multiple shots may observe the same performance without duplicating or independently generating the underlying actions.

### **8.2 Camera model**

A camera asset includes its world transform, projection model, sensor dimensions, focal length, focus distance, aperture, exposure parameters, and movement trajectory.

The fundamental projection is:

p\~∼KR∣tPw\\tilde p \\sim KRmidtP\_wp\~∼KR∣tPw

This transforms world-space geometry into camera-space image coordinates.

The 3D renderer then resolves visibility, surfaces, shading, and lighting to produce 2D frames.

### **8.3 Camera operator**

The camera operator translates high-level cinematic instructions into executable trajectories.

Supported MVP commands should include `static`, `follow`, `track`, `dolly`, `pan`, `tilt`, and `orbit`.

Example:

JSON

{  
  "camera\_id": "camera\_a",  
  "shot\_id": "shot\_03",  
  "lens\_mm": 35,  
  "movement": {  
    "type": "follow",  
    "subject": "alice",  
    "relative\_position": "behind",  
    "distance\_m": 2.0  
  },  
  "event\_instructions": \[  
    {  
      "event": "fridge\_door\_opening",  
      "operation": "orbit",  
      "direction": "right",  
      "degrees": 45  
    }  
  \]  
}

The camera operator must resolve this instruction into a time-dependent position and orientation, with appropriate smoothing.

### **8.4 Camera constraints**

The planner should evaluate framing, visibility, obstacle clearance, and motion smoothness.

An illustrative optimization objective is:

min⁡C(λfLframing+λoLocclusion+λcLcollision+λsLsmoothness)\\min\_C \\left( \\lambda\_f L\_{\\text{framing}} \+\\lambda\_o L\_{\\text{occlusion}} \+\\lambda\_c L\_{\\text{collision}} \+\\lambda\_s L\_{\\text{smoothness}} \\right)Cmin(λfLframing+λoLocclusion+λcLcollision+λsLsmoothness)

These terms are not equally important for every shot. A handheld shot may intentionally permit irregular motion, while a dolly shot should typically be smoother.

The director can explicitly authorize impossible camera moves, but accidental wall penetration should be detected.

### **8.5 Event synchronization**

Camera instructions may depend on action events instead of fixed timestamps.

For example, the camera begins orbiting when the refrigerator door starts opening.

If the character's performance is retimed, the camera plan can adapt without requiring the director to manually update every keyframe.

## **9\. Lighting and environment rendering**

Lighting is part of the persistent production setup.

Light sources have positions, orientations, intensities, colors, shapes, and animation parameters. Environment lighting may include sunlight, windows, practical lights, and ambient illumination.

The system should support lighting presets while preserving the ability to adjust individual sources.

A lighting setup may be shared across several shots, while exposure and camera-specific optical settings can vary.

The renderer should output a conventional RGB preview and, where supported, additional structural passes such as depth, normals, object segmentation, motion vectors, and lighting information.

The MVP does not require photorealistic 3D assets. It requires geometry and appearance references that are sufficient to support the intended interactions and downstream synthesis.

## **10\. Generative video rendering**

### **10.1 Purpose**

The generative renderer converts the virtual production's structural output into the desired final visual style.

Its inputs may include:

* RGB previews and structural rendering passes.  
* Persistent character and environment appearance references.  
* Camera and lighting metadata.  
* Temporal information and neighboring frames.  
* Style instructions.

Its outputs are video frames or clips, plus generation metadata.

### **10.2 Authority boundary**

The renderer is responsible for visual synthesis, not deciding what happened in the scene.

It should preserve object identity, spatial relationships, camera movement, and action timing.

However, this cannot be guaranteed simply by defining an interface. It must be demonstrated experimentally with the actual model and conditioning mechanism.

### **10.3 Fallback rendering**

The system must retain a non-generative rendering path.

If refinement introduces unacceptable distortions, users should still be able to view and export the original 3D render.

This also creates a baseline for comparing generative output against intended geometry and motion.

### **10.4 Long sequences**

The engine should maintain one continuous world and action timeline, even if the video model can only process shorter clips.

Long shots may require overlapping generation windows, boundary reconciliation, or alternative rendering methods.

The MVP should not assume that independently generating adjacent clips will automatically produce seamless motion.

## **11\. Execution workflow**

The end-to-end production process consists of seven stages.

1. Compile screenplay  
   Extract scenes, characters, props, actions, dependencies, and creative instructions. Present ambiguous decisions for review.  
2. Prepare assets  
   Retrieve or generate persistent character, environment, and prop assets. Validate required rigs and interaction affordances.  
3. Build world  
   Instantiate assets, establish spatial and semantic relationships, and initialize authoritative state.  
4. Plan and execute actions  
   Resolve semantic actions into motion primitives, animate characters and props, and record state transitions.  
5. Plan cinematography  
   Select shots, cameras, lenses, movement, lighting, and focus. Synchronize camera instructions with action events.  
6. Render and refine  
   Produce structural frames and conventional RGB previews. Optionally apply generative video refinement.  
7. Verify and edit  
   Inspect continuity, geometry, interaction correctness, camera adherence, and visual quality. Regenerate only the affected outputs where possible.

### **11.1 Dependency tracking**

Each generated artifact should record its dependencies.

For example:

shot\_03\_final\_video  
  ├── shot\_03\_camera\_v4  
  ├── kitchen\_lighting\_v2  
  ├── alice\_character\_v3  
  ├── kitchen\_environment\_v1  
  ├── action\_timeline\_v5  
  ├── structural\_render\_v6  
  └── refinement\_config\_v2

If the director changes the camera trajectory, the system should invalidate the relevant camera-dependent renders and final video, but retain the approved character asset and underlying action performance.

If an earlier action changes the world state, downstream animation and shots may also need invalidation.

A dependency graph is therefore preferable to an unconditional full-pipeline regeneration.

## **12\. Verification and quality control**

Verification should be split into deterministic checks and perceptual checks.

|  
Category

|

Example validation

|  
| \--- | \--- |  
|

Asset integrity

|

Referenced characters and props exist and have compatible rigs.

|  
|

World state

|

Object locations and ownership follow valid transitions.

|  
|

Motion

|

Character reaches target; joint limits and collisions are respected.

|  
|

Interaction

|

Hand-object contact and attachment timing are consistent.

|  
|

Camera

|

Subject is visible; camera follows the planned trajectory.

|  
|

Rendering

|

Structural passes are synchronized and contain valid data.

|  
|

Generated video

|

Character identity, object identity, geometry, and camera movement are preserved.

|  
|

Continuity

|

Adjacent shots agree on relevant state and appearance.

|

The system should distinguish a verified 3D simulation from a verified final video. Passing collision checks in 3D does not prove that a generative renderer preserved those contacts.

The MVP should expose side-by-side structural and final-video playback so reviewers can identify which stage introduced a failure.

## **13\. MVP definition**

### **13.1 Demonstration sequence**

The initial benchmark is a 15–30-second sequence:

> Alice approaches a house, opens the front door, enters, walks to the kitchen, opens the refrigerator, retrieves a soda can, and closes the refrigerator.

The sequence should support both a continuous tracking-camera plan and an edited multi-shot version of the same performance.

### **13.2 Supported content**

## **MVP scope**

Characters

# **1–2**

Persistent rigged identities

Locations

# **1**

House with connected entry and kitchen

Core actions

# **6–10**

Walking, turning, reaching, grasping, opening, carrying, releasing

Camera modes

# **3–4**

Static, follow, dolly, orbit

Planning targets, not empirically validated capacity limits.

### **13.3 Acceptance criteria**

The prototype is successful if it can:

1. Execute the entire action sequence in a persistent 3D world without invalid object-state transitions.  
2. Produce a camera trajectory that follows Alice through the doorway and kitchen without unintended collisions.  
3. Regenerate the sequence from a different camera angle while preserving the underlying performance and world state.  
4. Produce structural renders with consistent geometry and object identities.  
5. Demonstrate a generative refinement result and identify whether it preserves or violates the intended actions.  
6. Allow a reviewer to modify a camera instruction without regenerating the character and environment assets.

The first five criteria should be evaluated independently. A visually attractive result must not conceal a failure of the world simulation or camera system.

## **14\. Technical strategy and implementation choices**

### **14.1 Build versus buy**

The initial system should integrate an existing 3D engine rather than implement rendering, skeletal animation, physics, and camera systems from first principles.

A practical candidate is Unreal Engine, with its existing cinematic sequencing, animation, camera, and rendering capabilities. Blender is another option for asset preparation and offline rendering.

The engine selection should be based on automation APIs, asset compatibility, rendering-pass support, licensing, deployment constraints, and developer familiarity.

The team should own the screenplay compiler, production representation, orchestration, semantic world model, action composition, continuity tracking, and verification logic.

### **14.2 Suggested subsystem boundaries**

production/  
  screenplay/  
  asset\_registry/  
  world\_model/  
  action\_planner/  
  motion\_runtime/  
  cinematography/  
  rendering/  
  refinement/  
  verification/  
  editor/

The world engine and rendering engine should communicate through explicit asset references, scene-state snapshots, and timeline definitions.

The LLM should not directly mutate the rendering engine through unrestricted commands. Its output should pass through schema validation and a deterministic execution layer.

### **14.3 Reproducibility**

A production manifest should record the screenplay version, asset versions, action-plan version, scene-state version, camera configuration, renderer settings, model version, and generation seed where supported.

This enables debugging and controlled comparisons between iterations.

## **15\. Key risks and mitigation**

|  
Risk

|

Impact

|

Mitigation

|  
| \--- | \--- | \--- |  
|

Video model ignores structural constraints

|

Final footage contradicts the simulation

|

Test this before major platform investment; retain conventional rendering fallback.

|  
|

Character identity drifts

|

Multi-shot continuity breaks

|

Persistent character assets, reference conditioning, and identity checks.

|  
|

Hand-object interactions fail

|

Common actions look implausible

|

Restrict object types, use explicit contact constraints, validate at critical frames.

|  
|

Camera planner produces invalid paths

|

Camera intersects geometry or loses the subject

|

Collision-aware planning and framing validation.

|  
|

Script interpretation is ambiguous

|

Incorrect or inconsistent production decisions

|

Typed intermediate representation, unresolved-decision tracking, human review.

|  
|

Asset preparation is expensive

|

Each new scene requires substantial manual work

|

Reusable asset registry, procedural environments, constrained initial settings.

|  
|

Regeneration costs become excessive

|

Slow iteration and poor economics

|

Dependency-aware caching, preview renders, selective regeneration.

|  
|

System complexity overwhelms the team

|

Integration stalls before a useful demo

|

One benchmark sequence, narrow action library, existing engine components.

|

Highest-priority risk: whether generative refinement can reliably preserve a moving-camera 3D performance involving character-object contact.

This should be evaluated before committing to a broad asset library or autonomous screenplay-to-film workflow.

## **16\. Development roadmap**

The following is an initial planning estimate for a team of approximately three to four experienced contributors, not a delivery commitment.

|  
Phase

|

Timeline

|

Deliverable

|  
| \--- | \--- | \--- |  
|

Feasibility spike

|

Weeks 1–4

|

Moving-camera structural render and generative-refinement benchmark

|  
|

World foundation

|

Months 2–3

|

Persistent room, character, props, action timeline, state transitions

|  
|

Cinematography

|

Months 3–4

|

Camera operator, event synchronization, lighting, structural passes

|  
|

Script integration

|

Months 4–5

|

Screenplay compiler, validated action plans, review workflow

|  
|

End-to-end prototype

|

Month 6

|

Complete benchmark sequence, alternate camera edit, verification report

|

The feasibility spike is a decision gate. If the video model cannot preserve the required geometry and interactions, the team should narrow the visual target, change the rendering approach, or focus on a conventional 3D filmmaking tool rather than proceed under an unvalidated assumption.

## **17\. Open design questions**

These are the most important decisions to resolve through prototypes rather than lengthy upfront specification.

|  
Question

|

Why it matters

|  
| \--- | \--- |  
|

How much 3D detail is required?

|

Determines asset cost and whether the renderer has sufficient structural guidance.

|  
|

What conditioning interface does the video model actually support?

|

Determines whether camera, geometry, and motion constraints can be enforced.

|  
|

Should the system generate one continuous performance or separate shot-specific performances?

|

Affects continuity, acting quality, editing flexibility, and computational cost.

|  
|

How should the camera operator resolve competing constraints?

|

Affects framing, collision avoidance, and creative control.

|  
|

How much motion should be procedural versus learned?

|

Determines coverage, realism, and debugging complexity.

|  
|

What is the minimum acceptable level of human intervention?

|

Defines the boundary between an assisted production tool and an autonomous system.

|  
|

What constitutes a successful final render?

|

Determines measurable quality gates and whether the product is commercially useful.

|

## **18\. Immediate next step: Architecture validation**

Before building the complete screenplay compiler, create a single manually specified scene in an existing 3D engine.

Animate a character opening a refrigerator and retrieving a can. Add a camera that follows the character and moves sideways to reveal the interaction.

Export a conventional RGB render and structural passes. Feed those into candidate generative-video workflows and compare the outputs with the original animation.

Measure whether the generated video preserves the camera trajectory, character identity, refrigerator geometry, hand-can contact, and can position.

This experiment isolates the most uncertain dependency without requiring the rest of the platform.

### **Final design thesis**

Build a persistent, executable virtual production rather than a collection of independently generated clips.

The screenplay defines intent. The world model establishes reality. The motion engine executes actions. The cinematography engine selects the audience's viewpoint. The renderer produces the image. The verifier checks whether the final footage remains faithful to the production.

The near-term goal is not autonomous feature-film generation. It is a controllable, reusable production pipeline that can make one short, coherent scene—and then make it again with a different camera, lighting setup, or visual treatment without starting from scratch.

