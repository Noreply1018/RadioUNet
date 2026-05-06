# RadioUNet Reproduction Plan

This project aims to reproduce the paper:

Ron Levie, Cagkan Yapar, Gitta Kutyniok, and Giuseppe Caire, "RadioUNet: Fast Radio Map Estimation with Convolutional Neural Networks," IEEE Transactions on Wireless Communications, 2021.

Local reference materials are stored in `reference/`. The old Word/Markdown draft was removed because it mixed a useful high-level summary with unverified reproduction assumptions.

## Reproduction Standard

The target is not only to run one example. The target is a traceable reproduction where each reported result is tied to:

- the paper section/table/figure being reproduced,
- the exact dataset split,
- the exact model variant,
- a versioned config file,
- a saved checkpoint,
- evaluation metrics,
- generated figures,
- the git commit used to run the experiment.

## Source Of Truth

Use these materials as the authoritative basis:

- Paper PDF: `reference/RadioUNet_1911.09002.pdf`
- Paper source: `reference/RadioUNet_paper_source/RadioUNet_paper_ver3.tex`
- Official code: `reference/RadioUNet/`
- Official dataset entry point: https://radiomapseer.github.io

## Key Paper Facts To Preserve

- RadioMapSeer has 700 maps.
- Each complete map has 80 transmitter locations.
- Radio maps are dense `256 x 256` grids, with 1 meter per pixel.
- Coarse simulations include DPM and IRT2.
- Higher-accuracy IRT4 simulations exist for the first two transmitters of each map.
- The official split is a deterministic shuffle with seed 42, then map index ranges:
  - train: 0 to 500
  - validation: 501 to 600
  - test: 601 to 699
- The clean baseline input is buildings plus transmitter location.
- RadioUNet_C uses no radio-map measurements.
- RadioUNet_S additionally uses sparse pathloss measurements.
- Official notebooks use threshold `0.2` for the simplest experiments.
- Official implementation uses a WNet: the first U-Net predicts the radio map, and the second U-Net improves/adapts the prediction.

## Experiment Ladder

### Stage 0: Dataset And Loader Verification

Goal: prove that the local RadioMapSeer copy matches the expected structure and that every loader path is valid.

Tasks:

- Download RadioMapSeer outside git-tracked paths, preferably `RadioMapSeer/`.
- Verify required directories:
  - `png/buildings_complete/`
  - `png/antennas/`
  - `gain/DPM/`
  - `gain/IRT2/`
  - `gain/IRT4/`
  - optional cars and missing-building directories.
- Render a sample panel:
  - building map,
  - Tx map,
  - DPM label,
  - IRT2 label,
  - IRT4 label when available.
- Confirm tensor shapes and value ranges.

Deliverables:

- dataset validation log,
- sample visualization figure,
- notes on any missing directories.

### Stage 1: Clean DPM Baseline

Goal: reproduce the simplest official path with high fidelity.

Config: `configs/c_dpm_thr2.yaml`

Corresponds to:

- `RadioUNet_C`
- complete building maps,
- no sparse measurements,
- DPM target,
- threshold `0.2`,
- official notebook `RadioWNet_c_DPM_Thr2.ipynb`.

Training sequence:

1. Train first U-Net.
2. Evaluate first U-Net on validation and test.
3. Train second U-Net with first U-Net frozen, matching official WNet behavior.
4. Evaluate both outputs.

Deliverables:

- checkpoint for first U-Net phase,
- checkpoint for second U-Net phase,
- MSE, NMSE, RMSE,
- representative prediction panels,
- runtime measurement.

### Stage 2: RadioUNet_S With Sparse Measurements

Goal: reproduce the sample-assisted version.

Settings:

- input channels: buildings, Tx, sparse measurements,
- random number of samples in the paper range,
- compare against RadioUNet_C and interpolation baselines when feasible.

Deliverables:

- metric curve versus number of samples,
- prediction panels with sample locations marked,
- comparison to the clean baseline.

### Stage 3: Transfer And Robustness

Goal: reproduce the harder parts of the paper.

Settings:

- missing buildings,
- random DPM/IRT2 simulation mixture,
- cars simulation,
- cars as input,
- sparse IRT4 adaptation.

Deliverables:

- IRT4 zero-shot metrics,
- sparse IRT4 adaptation metrics,
- selected table rows from the paper,
- explanation of any divergence.

## Engineering Plan

The `reference/` directory is read-only source material. Reproduction code lives under `src/radiounet/`.

Initial migration:

- `src/radiounet/data.py` starts as a copy of official `lib/loaders.py`.
- `src/radiounet/models.py` starts as a copy of official `lib/modules.py`.

The first priority is fidelity. Refactors should be small and backed by tests or equivalence checks against the reference code.

Planned command entry points:

- `scripts/validate_dataset.py`
- `scripts/train.py`
- `scripts/evaluate.py`
- `scripts/make_figures.py`

## Metrics

Report at least:

- MSE over all pixels,
- NMSE using the same denominator as the official notebooks,
- RMSE over all pixels,
- RMSE converted to dB where the paper uses that convention,
- inference runtime per map.

For each metric, record whether it was computed on:

- first U-Net output,
- second U-Net output,
- dense DPM/IRT2 labels,
- dense IRT4 labels,
- sparse IRT4 sample points.

## Immediate Next Steps

1. Implement dataset validation script.
2. Implement train/evaluate scripts around `configs/c_dpm_thr2.yaml`.
3. Run a smoke test with a tiny custom subset.
4. Run full Stage 1 if hardware and dataset availability allow.
