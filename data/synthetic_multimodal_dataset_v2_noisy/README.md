# Synthetic Multimodal Dataset v2 (Noisy)

- Type: synthetic noisy dataset (for robustness testing)
- Samples: 220
- Label distribution: {'normal': 77, 'mci_risk': 88, 'high_risk': 55}
- Characteristics:
  - dialect-heavy composition
  - higher missing values
  - lower audio quality & more outliers
  - higher annotation noise vs v1

## Files
- dataset_master.csv
- feature_voice.csv
- feature_drawing.csv
- feature_behavior.csv
- feature_questionnaire.csv

## Important
1. Synthetic only, not clinical evidence.
2. Use with v1 for stress/ablation/robustness comparison.

## Missing-rate snapshot
{'master': {'sample_id': 0.0, 'participant_id': 0.0, 'session_id': 0.0, 'collect_date': 0.0, 'community_id': 0.0, 'age': 0.0, 'sex': 0.0, 'education_years': 0.0, 'device_type': 0.0, 'language_dialect': 0.0, 'mmse_raw': 0.023, 'moca_raw': 0.045, 'moca_edu_corrected': 0.064, 'doctor_label': 0.0, 'consensus_label': 0.0, 'label_source': 0.0, 'label_confidence': 0.0, 'retest_required': 0.0, 'exclude_flag': 0.0, 'exclude_reason': 0.918, 'split': 0.0}, 'voice': {'sample_id': 0.0, 'voice_task_id': 0.0, 'duration_sec': 0.041, 'word_count': 0.064, 'speech_rate': 0.073, 'pause_count': 0.068, 'snr_score': 0.045, 'asr_text': 0.1, 'audio_url': 0.105}, 'drawing': {'sample_id': 0.0, 'drawing_task_id': 0.0, 'stroke_count': 0.091, 'total_points': 0.114, 'clock_layout_score': 0.082, 'hand_angle_score': 0.1, 'image_url': 0.105}, 'behavior': {'sample_id': 0.0, 'reaction_time_mean_ms': 0.068, 'reaction_time_std_ms': 0.068, 'fast_ratio': 0.109, 'slow_ratio': 0.077, 'answer_modify_count': 0.064, 'click_accuracy': 0.086}, 'questionnaire': {'sample_id': 0.0, 'question_count': 0.0, 'choice_accuracy': 0.055, 'scale_mean': 0.068, 'domain_memory': 0.059, 'domain_attention': 0.073, 'domain_language': 0.068, 'domain_visuospatial': 0.036, 'domain_executive': 0.041, 'domain_orientation': 0.064}}