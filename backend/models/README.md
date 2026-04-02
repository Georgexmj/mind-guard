# Deep Model Checkpoints

Place deep multimodal checkpoints here.

Default path used by backend config:

- `models/deep_multimodal_fusion.pt`

Training example:

```bash
cd backend
python -m scripts.train_deep_multimodal --input ../data/deep_train.csv --output models/deep_multimodal_fusion.pt
```

