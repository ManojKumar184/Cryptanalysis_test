# Cryptoanalysis V3 --- Complete System Design

**Repository:** `ManojKumar184/Cryptanalysis_test`\
**Deployment:** Hugging Face Space, Docker-based\
**Purpose:** Continual active-learning research system for learning
whether legal Bitcoin-style candidate modifications can be
selected/generated increasingly efficiently using SHA-256d computational
structure and candidate-specific internal states.

## 1. Non-negotiable requirements

-   Candidate is represented as `C(F,M)`.
-   `F` is the fixed portion; `M` is the mutable portion.
-   `M` contains only explicitly enabled, Bitcoin-consensus-permitted
    mutable components.
-   The system continuously observes, learns, modifies, evaluates, and
    updates.
-   There is no separate fixed training phase as the main operating
    mode.
-   Actual candidate-specific SHA-256d internal states must be available
    to the learning system.
-   The fixed SHA-256d computation structure is represented separately
    and encoded by a GNN.
-   Base and modified internal-state trajectories must be representable,
    including their differences.
-   Exact SHA-256d and exact target comparison are ground truth.
-   The AI cannot define success or alter cryptographic rules.
-   Learn from both successes and failures.
-   Experience persists indefinitely, subject only to physical storage.
-   No fixed event cap.
-   No fixed training-data cap.
-   No fixed experiment duration.
-   No sequential search.
-   No AI-vs-sequential benchmark.
-   No random baseline.
-   Primary objective: minimize exact SHA-256d evaluations needed to
    find a successful legal modification.
-   Ideal target: success on the first modification.
-   The system must survive restart and resume from persistent state.
-   Runtime data must be stored on persistent Hugging Face storage.
-   Checkpoints must be atomic and recoverable.
-   Model versions must be auditable.
-   Do not call training-loss reduction alone "improvement".
-   Measure SHA work, state-trace work, inference, training, and
    wall-clock cost separately.
-   Autonomous mode must not start until integrity tests pass.

## 2. Repository structure

``` text
Cryptanalysis_test/
├── README.md
├── Dockerfile
├── requirements.txt
├── app.py
├── worker.py
│
├── config/
│   └── config.yaml
│
├── core/
│   ├── __init__.py
│   ├── block.py
│   ├── bitcoin_rules.py
│   ├── modifications.py
│   ├── sha256.py
│   ├── sha256d.py
│   ├── sha_trace.py
│   ├── target.py
│   └── evaluator.py
│
├── representations/
│   ├── __init__.py
│   ├── sha_graph.py
│   ├── state_encoder.py
│   └── difference.py
│
├── models/
│   ├── __init__.py
│   ├── gnn.py
│   ├── difference_model.py
│   ├── ranking_model.py
│   └── generator.py
│
├── learning/
│   ├── __init__.py
│   ├── experience.py
│   ├── database.py
│   ├── replay.py
│   ├── trainer.py
│   └── model_manager.py
│
├── experiment/
│   ├── __init__.py
│   ├── controller.py
│   ├── candidate_stream.py
│   ├── search.py
│   └── improvement.py
│
├── persistence/
│   ├── __init__.py
│   ├── checkpoint.py
│   └── recovery.py
│
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py
│   ├── logger.py
│   └── dashboard.py
│
└── tests/
    ├── __init__.py
    ├── test_sha256.py
    ├── test_sha256d.py
    ├── test_trace.py
    ├── test_block.py
    ├── test_modifications.py
    ├── test_evaluator.py
    ├── test_database.py
    ├── test_checkpoint.py
    ├── test_recovery.py
    └── test_models.py
```

## 3. Top-level files

### `app.py`

Hugging Face web/dashboard entry point. Starts or connects to the
worker, displays persistent experiment state, logs, metrics, model
version, candidate, attempt count, and recovery status. It must not
contain cryptographic or learning logic.

### `worker.py`

Starts the autonomous controller, performs startup/recovery checks, runs
the continual-learning loop, handles graceful shutdown, and keeps the
worker restart-safe.

### `Dockerfile`

Reproducible Hugging Face container. Installs dependencies, copies
application code, establishes the runtime entry point, and supports the
dashboard plus background worker.

### `requirements.txt`

Pinned or appropriately constrained runtime dependencies. Avoid
unnecessary packages.

### `README.md`

Documents architecture, scientific objective, deployment,
persistent-storage requirement, recovery behavior, tests, configuration,
and the fact that this is an experimental continual-learning system
rather than a claim that SHA-256d is predictable.

## 4. Core cryptographic layer

### `core/block.py`

First-class `Candidate`/block representation.

Represent:

``` text
C(F,M)
F = fixed fields
M = mutable fields
serialized representation
unique candidate ID
metadata
```

Keep fixed and mutable portions explicit.

### `core/bitcoin_rules.py`

Central source of truth for which fields are legal to modify in this
experiment. Validate field ranges, serialization rules, and
consensus-related constraints applicable to the experimental candidate
representation.

No model may bypass this layer.

### `core/modifications.py`

First-class `Modification` object and modification generation/validation
interfaces.

Must: - reject illegal changes; - reject no-ops; - detect duplicate
resulting candidates; - record before/after values; - record which
mutable fields changed; - produce deterministic serialized candidates.

### `core/sha256.py`

Exact SHA-256 implementation.

Provide: - normal digest mode; - compression-level trace mode; -
verified behavior against `hashlib.sha256`.

### `core/sha256d.py`

Exact double-SHA-256 implementation.

Provide normal and trace-capable interfaces.

### `core/sha_trace.py`

Defines the internal execution trace schema.

For each compression pass expose the sequence of internal states:

``` text
S0 ... S63
```

For SHA-256d, explicitly represent both passes.

The trace must be candidate-specific.

### `core/target.py`

Exact target representation and digest-vs-target comparison.

### `core/evaluator.py`

Ground-truth evaluator: 1. accept only a validated candidate; 2. compute
exact SHA-256d; 3. compare with target; 4. return digest,
success/failure, and relevant measurements; 5. never use AI predictions
as ground truth.

## 5. SHA representation layer

### `representations/sha_graph.py`

Static SHA-256d computation graph.

Represent relevant: - round index; - pass identity; - message-schedule
dependencies; - state dependencies; - SHA constants; - structural
metadata.

This is mechanism/topology information, not candidate-specific
execution.

### `representations/state_encoder.py`

Convert actual internal traces into model tensors while preserving: -
pass identity; - round order; - base vs modified identity; - state-word
structure; - normalization rules.

### `representations/difference.py`

Compute a deterministic representation of the perturbation between base
and modified trajectories.

Conceptually:

``` text
base states
modified states
      ↓
Δ-state trajectory
```

Keep the representation replaceable so modular difference, XOR/bit, or
other encodings can be tested without rewriting the rest of the system.

## 6. AI models

### `models/gnn.py`

Mechanism encoder operating on the static SHA-256d graph.

Output: mechanism embedding.

### `models/difference_model.py`

Learns the relationship between: - candidate; - legal modification; -
base internal states; - modified internal states; - state differences; -
mechanism embedding.

Its research purpose is to test whether modification-induced
internal-state consequences contain learnable information.

Do not assume success prediction before evidence supports it.

### `models/ranking_model.py`

Combines: - candidate representation; - modification representation; -
mechanism embedding; - state/difference representation; - historical
experience.

Outputs a modification ranking score and optional diagnostic
predictions.

Operational purpose: put promising legal modifications earlier.

### `models/generator.py`

Modification proposal system.

Initial stage: propose within a formally defined legal modification
space.

Later stage: learn to propose modifications from accumulated experience.

Every generated modification must pass `bitcoin_rules.py` and
`modifications.py`.

## 7. Continual learning

### `learning/experience.py`

Defines the canonical experience record.

At minimum:

``` text
candidate ID
attempt index
modification
modified candidate
model version
prediction/score
exact digest
target
success/failure
Q if calculated
state/difference references
timings
timestamp
```

### `learning/database.py`

Persistent SQLite database.

Recommended tables:

``` text
candidates
attempts
successes
models
training_runs
checkpoints
events
metrics
```

Use transactions.

An attempt is not committed until the complete result is durably
recorded.

### `learning/replay.py`

Samples from the complete historical archive for continual updates.

The archive remains unbounded by experiment design. Replay minibatch
size is a computational parameter, not a training-data cap.

Use a mixture of recent experience, historical experience, successes,
failures, and useful hard examples to reduce catastrophic forgetting.

### `learning/trainer.py`

Performs continual model updates.

There is no fixed Dataset A/B workflow.

Each observed attempt becomes available to future learning after its
result is committed.

### `learning/model_manager.py`

Immutable model versioning.

Example:

``` text
model_000001
model_000002
...
```

Record parent version, training update, experience count, metrics,
timestamp, and promotion decision.

Never silently replace the active model with an unverified worse
version.

## 8. Experiment layer

### `experiment/candidate_stream.py`

Produces the next candidate after the current candidate reaches success.

Each candidate gets a unique persistent ID.

For chained Bitcoin-style experiments, construct the next candidate
context from the successful predecessor where applicable.

Persist the stream state so restart cannot silently reset it.

### `experiment/search.py`

Core modification loop:

``` text
candidate
  ↓
analyze
  ↓
mechanism/state representations
  ↓
AI proposes legal modification
  ↓
validate
  ↓
exact SHA-256d
  ↓
record
  ↓
learn
  ↓
next modification on failure
  ↓
next candidate on success
```

Do not impose an artificial attempt/event cap.

### `experiment/controller.py`

Explicit persistent state machine:

``` text
INITIALIZING
RECOVERING
CREATING_CANDIDATE
ANALYZING
GENERATING_MODIFICATION
VALIDATING_MODIFICATION
EVALUATING
RECORDING
LEARNING
CHECKPOINTING
SUCCESS
NEXT_CANDIDATE
PAUSED
ERROR
```

Persist enough state to recover from any normal interruption.

### `experiment/improvement.py`

Tracks the actual research objective:

``` text
exact SHA evaluations to first success
success@1
success@2
success@5
success@10
success@25
success@50
success@100
...
```

Also track model version, rolling/lifetime statistics, state-trace cost,
inference cost, training cost, and wall-clock cost.

Do not define improvement solely from training loss or AUC.

## 9. Persistence

### `persistence/checkpoint.py`

Atomic checkpoints containing: - active model version; - model
weights; - optimizer/scheduler state; - current candidate; - attempt
index; - controller state; - experience position; - counters; - relevant
random state; - configuration version; - consistency metadata.

Checkpoint after important state transitions, after successes,
periodically, and during graceful shutdown.

Never overwrite the only valid checkpoint.

### `persistence/recovery.py`

On startup:

``` text
validate persistent storage
→ validate database
→ find newest valid checkpoint
→ verify integrity
→ restore model
→ restore controller
→ reconcile DB/checkpoint
→ resume
```

If the newest checkpoint is corrupt, use the newest previous valid
checkpoint.

Prevent duplicate committed attempts after restart.

## 10. Monitoring

### `monitoring/logger.py`

Structured persistent logs with events such as:

``` text
EXPERIMENT_STARTED
EXPERIMENT_RESUMED
CANDIDATE_CREATED
ATTEMPT_STARTED
ATTEMPT_COMPLETED
SUCCESS_FOUND
EXPERIENCE_COMMITTED
TRAINING_STARTED
TRAINING_COMPLETED
MODEL_CREATED
MODEL_PROMOTED
MODEL_REJECTED
CHECKPOINT_CREATED
CHECKPOINT_RECOVERED
PAUSED
ERROR
```

### `monitoring/metrics.py`

Persistent metrics: - candidate count; - attempt count; - success
count; - experience count; - attempts/success; - success@K; - model
version; - training metrics; - cryptographic computation time; -
state-trace time; - inference time; - training time; - wall-clock time.

### `monitoring/dashboard.py`

Dashboard showing current status, candidate, attempt, model version,
lifetime counters, rolling performance, learning trend, model history,
last checkpoint, last success, and errors.

The dashboard is observational and cannot change cryptographic ground
truth.

## 11. Configuration

### `config/config.yaml`

Keep experiment/runtime configuration centralized.

Example categories:

``` yaml
experiment:
  continual_learning: true

search:
  trace_mode: selected

learning:
  replay:
    enabled: true

checkpoint:
  interval: configurable

persistence:
  root: /data/cryptoanalysis
```

Do not put credentials in configuration files.

Do not introduce forbidden caps or baselines.

## 12. Hugging Face deployment design

Use a Docker Space.

Runtime persistent data:

``` text
/data/cryptoanalysis/
├── database/
├── checkpoints/
├── models/
├── metrics/
└── logs/
```

Ordinary container filesystem must be treated as ephemeral.

The application should refuse autonomous execution if required
persistent storage is unavailable.

Startup:

``` text
start
→ persistence check
→ integrity checks
→ DB open
→ checkpoint recovery
→ model recovery
→ controller recovery
→ worker starts/resumes
```

Shutdown:

``` text
SIGTERM
→ stop starting new work
→ finish safe current transaction
→ checkpoint
→ flush DB
→ exit
```

A container restart is normal and must not reset the experiment.

## 13. Data leakage rules

Before a proposed modification is evaluated, the AI may use: - current
candidate; - fixed/mutable candidate representation; - allowed current
internal-state information; - SHA structural representation; -
accumulated historical experience.

It must not receive: - future digest of the proposed candidate; -
success/failure of the proposed candidate; - target-comparison result of
the proposed candidate.

After evaluation, the outcome becomes experience.

Audit feature-building functions specifically for final-hash/success
leakage.

## 14. Computational accounting

Separate:

``` text
exact SHA-256d evaluations
internal-state trace computations
feature-generation time
AI inference time
AI training time
total wall-clock time
```

Do not hide substantial cryptographic work inside feature generation.

## 15. Testing gates

Autonomous mode remains disabled until all tests pass.

### Cryptography

-   SHA-256 known vectors;
-   randomized comparison with `hashlib`;
-   SHA-256d;
-   target comparison;
-   trace consistency.

### Candidate/modification

-   serialization;
-   legal field validation;
-   illegal modification rejection;
-   no-op rejection;
-   duplicate detection;
-   deterministic mutation.

### Persistence

-   SQLite transaction tests;
-   checkpoint save/load;
-   atomic checkpoint behavior;
-   corruption fallback;
-   restart recovery;
-   duplicate-commit prevention.

### Models

-   forward passes;
-   tensor shapes;
-   state encoder;
-   difference representation;
-   model save/load;
-   optimizer save/load.

### Controller

-   failure path;
-   success path;
-   next-candidate path;
-   learning update;
-   checkpoint path;
-   recovery path.

### Deployment

-   Docker build;
-   Space startup;
-   persistent storage detection;
-   dashboard startup;
-   worker startup;
-   graceful shutdown.

## 16. Implementation order

Do not write the entire system as one untested batch.

### Phase 1 --- Cryptographic foundation

Implement and test:

``` text
core/sha256.py
core/sha256d.py
core/sha_trace.py
core/target.py
core/evaluator.py
representations/state_encoder.py
```

### Phase 2 --- Candidate/modification foundation

Implement and test:

``` text
core/block.py
core/bitcoin_rules.py
core/modifications.py
```

### Phase 3 --- AI representations/models

Implement and test:

``` text
representations/sha_graph.py
representations/difference.py
models/gnn.py
models/difference_model.py
models/ranking_model.py
models/generator.py
```

### Phase 4 --- Continual learning

Implement and test:

``` text
learning/experience.py
learning/database.py
learning/replay.py
learning/trainer.py
learning/model_manager.py
```

### Phase 5 --- Autonomous experiment/persistence

Implement and test:

``` text
persistence/checkpoint.py
persistence/recovery.py
experiment/candidate_stream.py
experiment/search.py
experiment/controller.py
experiment/improvement.py
```

### Phase 6 --- Monitoring/deployment

Implement:

``` text
monitoring/logger.py
monitoring/metrics.py
monitoring/dashboard.py
app.py
worker.py
```

### Phase 7 --- Docker/Hugging Face

Implement:

``` text
Dockerfile
requirements.txt
deployment configuration
```

Then perform deployment tests before autonomous mode.

## 17. Critical differences from the old experiment

The old positive-result code had a static SHA graph and
candidate/modification features, but it did not feed actual
candidate-specific intermediate state trajectories into the model.

V3 must have:

``` text
static SHA-256d graph
+
actual candidate-specific internal states
+
base/modified state differences
+
continual learning
+
persistent experience
+
indefinite operation
+
checkpoint/recovery
+
model versioning
```

Do not copy the old experiment wholesale.

## 18. Definition of success for the project

The software is complete only when:

1.  Exact SHA-256d is verified.
2.  Internal-state traces are verified.
3.  `C(F,M)` is explicit.
4.  Legal modifications are enforced.
5.  AI actually receives candidate-specific internal-state tensors.
6.  Continual learning works.
7.  Experience persists.
8.  Models persist and are versioned.
9.  Checkpoints work.
10. Crash recovery works.
11. No duplicate committed attempts occur.
12. No sequential/random baselines exist.
13. No artificial event/training-data caps exist.
14. Improvement statistics persist.
15. Dashboard reflects actual runtime state.
16. Docker builds.
17. Hugging Face starts.
18. Persistent storage is detected.
19. Graceful shutdown works.
20. Restart resumes from the last consistent state.
21. Autonomous mode is enabled only after integrity tests pass.

## 19. Codex implementation instructions

When taking this specification into Codex:

1.  Inspect the existing repository first.
2.  Do not overwrite existing files blindly.
3.  Review existing code before reusing it.
4.  Build the architecture phase-by-phase.
5.  Run tests after every major phase.
6.  Fix failures before moving forward.
7.  Preserve the research objective exactly.
8.  Do not introduce sequential search, random baseline, event caps, or
    training-data caps.
9.  Do not claim internal-state input exists unless actual
    candidate-specific state tensors reach the model.
10. Never expose future evaluation outcomes to the predictor before
    evaluation.
11. Keep cryptographic ground truth independent of AI.
12. Make every important runtime state recoverable.
13. Keep all runtime data on persistent Hugging Face storage.
14. Preserve model versions and experiment history.
15. Document unresolved assumptions rather than silently inventing them.
16. Do not activate indefinite autonomous execution until all integrity
    tests pass.

## 20. Final conceptual system

``` text
NEW CANDIDATE C(F,M)
        |
        +--> SHA-256d structural graph --> GNN
        |
        +--> actual internal states
        |
        +--> base/modified state differences
        |
        v
DIFFERENCE / CONSEQUENCE MODEL
        |
        v
RANKING MODEL
        |
        v
MODIFICATION GENERATOR
        |
        v
LEGALITY VALIDATOR
        |
        v
MODIFIED CANDIDATE
        |
        v
EXACT SHA-256d
        |
   +----+----+
   |         |
FAILURE   SUCCESS
   |         |
   +----+----+
        |
        v
PERSIST EXPERIENCE
        |
        v
CONTINUAL UPDATE
        |
        v
CHECKPOINT
        |
        v
NEXT MODIFICATION
        |
   success?
        |
        v
NEXT CANDIDATE
        |
       ...
```

The system runs continuously, learns from accumulated experience, and
attempts to improve its modification strategy toward the ideal of
finding a successful legal modification immediately. This is an
experimental hypothesis to be tested, not an assumption that SHA-256d
contains a practically exploitable predictive signal.
