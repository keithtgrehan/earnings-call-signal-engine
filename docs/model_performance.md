# Model Performance

Model artifacts root: `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/models/multimodal_engine`.

The current text baseline is a fixture/seed-label baseline. It proves the training and tracking loop, but it is not a validated model and should not be presented as production performance.

## Training Status

```json
{
  "stage": "train",
  "status": "completed",
  "readiness": {
    "ready": true,
    "total_examples": 48,
    "label_support": {
      "risk_friction": 12,
      "opportunity_commitment": 13,
      "uncertainty_hedging": 12,
      "neutral": 11
    },
    "minimum_examples_per_class": 2,
    "minimum_total_examples": 12,
    "insufficient_labels": [],
    "reason": "weak-label corpus is ready for a bounded train/test split"
  },
  "text_model": {
    "status": "completed",
    "examples": 48,
    "best_model": "tfidf_linear_svc",
    "best_macro_f1": 0.7595,
    "model_path": "/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/models/multimodal_engine/text_signal_baseline.joblib",
    "models": {
      "tfidf_logistic_regression": {
        "accuracy": 0.75,
        "macro_f1": 0.7321428571428572,
        "weighted_f1": 0.7321428571428571,
        "per_label": {
          "risk_friction": {
            "tp": 1,
            "fp": 0,
            "fn": 2,
            "support": 3,
            "precision": 1.0,
            "recall": 0.3333333333333333,
            "f1": 0.5
          },
          "opportunity_commitment": {
            "tp": 2,
            "fp": 2,
            "fn": 1,
            "support": 3,
            "precision": 0.5,
            "recall": 0.6666666666666666,
            "f1": 0.5714285714285715
          },
          "uncertainty_hedging": {
            "tp": 3,
            "fp": 1,
            "fn": 0,
            "support": 3,
            "precision": 0.75,
            "recall": 1.0,
            "f1": 0.8571428571428571
          },
          "neutral": {
            "tp": 3,
            "fp": 0,
            "fn": 0,
            "support": 3,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0
          }
        },
        "confusion_matrix": {
          "risk_friction": {
            "risk_friction": 1,
            "opportunity_commitment": 2,
            "uncertainty_hedging": 0,
            "neutral": 0
          },
          "opportunity_commitment": {
            "risk_friction": 0,
            "opportunity_commitment": 2,
            "uncertainty_hedging": 1,
            "neutral": 0
          },
          "uncertainty_hedging": {
            "risk_friction": 0,
            "opportunity_commitment": 0,
            "uncertainty_hedging": 3,
            "neutral": 0
          },
          "neutral": {
            "risk_friction": 0,
            "opportunity_commitment": 0,
            "uncertainty_hedging": 0,
            "neutral": 3
          }
        }
      },
      "tfidf_linear_svc": {
        "accuracy": 0.75,
        "macro_f1": 0.7595238095238095,
        "weighted_f1": 0.7595238095238095,
        "per_label": {
          "risk_friction": {
            "tp": 2,
            "fp": 0,
            "fn": 1,
            "support": 3,
            "precision": 1.0,
            "recall": 0.6666666666666666,
            "f1": 0.8
          },
          "opportunity_commitment": {
            "tp": 2,
            "fp": 2,
            "fn": 1,
            "support": 3,
            "precision": 0.5,
            "recall": 0.6666666666666666,
            "f1": 0.5714285714285715
          },
          "uncertainty_hedging": {
            "tp": 2,
            "fp": 1,
            "fn": 1,
            "support": 3,
            "precision": 0.6666666666666666,
            "recall": 0.6666666666666666,
            "f1": 0.6666666666666666
          },
          "neutral": {
            "tp": 3,
            "fp": 0,
            "fn": 0,
            "support": 3,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0
          }
        },
        "confusion_matrix": {
          "risk_friction": {
            "risk_friction": 2,
            "opportunity_commitment": 1,
            "uncertainty_hedging": 0,
            "neutral": 0
          },
          "opportunity_commitment": {
            "risk_friction": 0,
            "opportunity_commitment": 2,
            "uncertainty_hedging": 1,
            "neutral": 0
          },
          "uncertainty_hedging": {
            "risk_friction": 0,
            "opportunity_commitment": 1,
            "uncertainty_hedging": 2,
            "neutral": 0
          },
          "neutral": {
            "risk_friction": 0,
            "opportunity_commitment": 0,
            "uncertainty_hedging": 0,
            "neutral": 3
          }
        }
      },
      "tfidf_sgd": {
        "accuracy": 0.6666666666666666,
        "macro_f1": 0.6309523809523809,
        "weighted_f1": 0.6309523809523809,
        "per_label": {
          "risk_friction": {
            "tp": 3,
            "fp": 3,
            "fn": 0,
            "support": 3,
            "precision": 0.5,
            "recall": 1.0,
            "f1": 0.6666666666666666
          },
          "opportunity_commitment": {
            "tp": 3,
            "fp": 1,
            "fn": 0,
            "support": 3,
            "precision": 0.75,
            "recall": 1.0,
            "f1": 0.8571428571428571
          },
          "uncertainty_hedging": {
            "tp": 1,
            "fp": 0,
            "fn": 2,
            "support": 3,
            "precision": 1.0,
            "recall": 0.3333333333333333,
            "f1": 0.5
          },
          "neutral": {
            "tp": 1,
            "fp": 0,
            "fn": 2,
            "support": 3,
            "precision": 1.0,
            "recall": 0.3333333333333333,
            "f1": 0.5
          }
        },
        "confusion_matrix": {
          "risk_friction": {
            "risk_friction": 3,
            "opportunity_commitment": 0,
            "uncertainty_hedging": 0,
            "neutral": 0
          },
          "opportunity_commitment": {
            "risk_friction": 0,
            "opportunity_commitment": 3,
            "uncertainty_hedging": 0,
            "neutral": 0
          },
          "uncertainty_hedging": {
            "risk_friction": 1,
            "opportunity_commitment": 1,
            "uncertainty_hedging": 1,
            "neutral": 0
          },
          "neutral": {
            "risk_friction": 2,
            "opportunity_commitment": 0,
            "uncertainty_hedging": 0,
            "neutral": 1
          }
        }
      }
    }
  },
  "multimodal_models": {
    "logistic_regression": "candidate_registered",
    "random_forest": "candidate_registered",
    "shallow_pytorch_nn": "candidate_registered",
    "status": "not_trained_without_aligned_multimodal_gold_labels"
  },
  "mlflow": {
    "available": true,
    "run_id": "14ed54bfc7064890913069ff28f52a56",
    "tracking_uri": "/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/processed/multimodal_engine/mlruns"
  }
}
```

The v1 run trains TF-IDF sklearn text baselines when local human-reviewed signal labels satisfy class-support gates. Logistic Regression, Random Forest, and shallow PyTorch multimodal models are registered as candidates but are not trained without aligned multimodal gold labels.
