# Computer Vision Strategy

**CV is Phase 4. We do not start it until the event-analytics core exists.**
This document is a feasibility plan, not a build order. Nothing here is
implemented yet, and we will **not** train large models from scratch — the plan
is pretrained models + fine-tuning + classical geometry.

## Why CV is a separate world from our event data

Our StatsBomb competitions have **no video**. SoccerNet video is **different
matches, different era**. So CV outputs (tracks, heatmaps) will initially be
demonstrated on SoccerNet/sample clips in isolation, not fused with the event
layer. Fusing them would need matching video to event data — out of scope.

## The CV pipeline (standard football-video stack)

```text
video frames
   │
   ▼
[1] player & ball detection      -> bounding boxes per frame
   │
   ▼
[2] multi-object tracking        -> consistent player IDs across frames
   │
   ▼
[3] team assignment              -> which team each track belongs to (jersey colour)
   │
   ▼
[4] pitch / line detection       -> find pitch landmarks in the image
   │
   ▼
[5] homography estimation        -> image pixels  ->  pitch coordinates (metres)
   │
   ▼
[6] analytics on pitch coords    -> heatmaps, distances covered, team shape,
                                     compactness, pitch control, off-ball runs
```

## Task-by-task plan

### [1] Player & ball detection

| | |
|---|---|
| Approach | Pretrained object detector (YOLO family / RT-DETR) fine-tuned on football |
| Data | SoccerNet-Tracking / SoccerNet-v3 bounding boxes; or roboflow football datasets |
| Hard parts | Ball is tiny, motion-blurred, often occluded; player pile-ups |
| Compute | Fine-tuning: 1 GPU, hours. Inference: real-time-ish on GPU |
| Classical alternative | None competitive |

### [2] Multi-object tracking

| | |
|---|---|
| Approach | Tracking-by-detection: ByteTrack / BoT-SORT / OC-SORT (motion + IoU); add re-ID embeddings for occlusions |
| Data | SoccerNet-Tracking (has IDs + jersey numbers) |
| Hard parts | ID switches when players cross; players leaving/entering frame; broadcast camera cuts |
| Compute | Light on top of detection |

### [3] Team assignment

| | |
|---|---|
| Approach | Cluster player-crop colour histograms / small CNN embeddings into 2 teams + referee + keepers; or jersey-number OCR |
| Hard parts | Similar kits, lighting, keepers, low-res crops |

### [4] Pitch / line detection

| | |
|---|---|
| Approach | Segmentation of pitch lines / keypoint detection of known landmarks (corners, centre circle, penalty box intersections) |
| Data | SoccerNet camera-calibration subset (has pitch annotations) |

### [5] Homography (image → pitch metres)

| | |
|---|---|
| Approach | Solve homography from ≥4 matched landmark points (classical `cv2.findHomography` + RANSAC); or a learned camera-calibration network for broadcast cameras |
| Hard parts | Broadcast camera pans/zooms every second → re-estimate per frame; few visible landmarks in tight shots |
| Why it matters | Without this, tracks are in pixels and useless for tactical metrics |

### [6] Analytics on pitch coordinates

Once players are in metres:

- **Heatmaps** per player / team (2D histogram or KDE of positions).
- **Team shape**: convex hull area, defensive-line height, width, compactness,
  distance between lines.
- **Pitch control** (Spearman-style model): probability each team controls each
  location — needs positions + velocities.
- **Off-ball runs**, pressing triggers, defensive coverage.

These same tactical metrics can be prototyped **now** on **Metrica sample data**
(3 matches, already in pitch coordinates) — no CV needed. That is the smart
order: learn the analytics on clean tracking data first, add the CV that produces
tracking data later.

## Datasets (see [dataset_research.md](dataset_research.md))

| Dataset | Role | Access constraint |
|---|---|---|
| SoccerNet-Tracking / v3 | detection + tracking training/eval | NDA form, non-commercial, large |
| SoccerNet camera calibration | pitch landmarks / homography | same |
| Metrica sample data | learn tracking analytics ([6]) with zero CV | permissive, only 3 matches |
| SkillCorner opendata | broadcast-tracking prototyping | CC-BY-NC, ~10 matches |
| IDSSE / DFL | synced tracking+events, 7 matches | research licence |

## Compute reality check

| Activity | Feasible on a laptop? | Needs GPU? |
|---|---|---|
| Running pretrained detection/tracking on a few clips | Slow but yes (CPU) | Strongly preferred |
| Fine-tuning a detector | No | Yes (Colab / cloud GPU, a few hours) |
| Full SoccerNet download | Needs 100s of GB disk | — |
| Tracking-data analytics on Metrica/SkillCorner | Yes, easily | No |

**Recommendation:** Phase 4 starts with (a) tracking analytics on Metrica data
(CPU, immediate) and (b) running *pretrained* YOLO+ByteTrack on a handful of
SoccerNet clips (Colab GPU). Fine-tuning and homography are stretch goals.

## Explicit non-goals for CV

- No from-scratch model training.
- No real-time / live video.
- No full automated tactical report from broadcast video.
- No claim of tracking accuracy comparable to commercial optical tracking.
- CV is a **learning spike and portfolio piece**, scoped to a few clips.
