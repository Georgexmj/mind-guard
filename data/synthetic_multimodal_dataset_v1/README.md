# Synthetic Multimodal Dataset v1

- Type: synthetic (for development/testing/demo)
- Samples: 180
- Label distribution: {'normal': 72, 'mci_risk': 72, 'high_risk': 36}
- Files:
  - dataset_master.csv
  - feature_voice.csv
  - feature_drawing.csv
  - feature_behavior.csv
  - feature_questionnaire.csv

## Notes
1. This dataset is synthetic and must not be used as clinical evidence.
2. Labels follow project-level screening rules and include mild annotation noise.
3. split column in master table: train/val/test.