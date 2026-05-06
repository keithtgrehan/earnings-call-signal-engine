# Source Quality Metric Comparison

| subset | rows | precision | recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| `all` | 57 | 0.8399 | 0.8326 | 0.8276 |
| `human_reviewed` | 12 | 0.6 | 0.6375 | 0.5794 |
| `fixture_excluded` | 21 | 0.6429 | 0.6833 | 0.646 |
| `high_quality` | 12 | 0.6 | 0.6375 | 0.5794 |
| `imported_guidance` | 9 | 0.75 | 0.75 | 0.75 |
| `fixture` | 36 | 0.8365 | 0.8045 | 0.7954 |

## Are Imported Or Fixture Labels Poisoning Metrics?

They are not poisoning the canonical file, but they do change interpretation. Fixture rows dominate the current gold set, while imported guidance rows expose important finance-language gaps. Product claims should be based on high-quality human-reviewed and fixture-excluded subsets as the label set grows.

```json
[
  {
    "subset": "all",
    "row_count": 57,
    "metrics": {
      "precision": 0.8399,
      "recall": 0.8326,
      "f1": 0.8276,
      "per_label": {
        "risk_friction": {
          "precision": 0.8571,
          "recall": 0.9231,
          "f1": 0.8889,
          "support": 13
        },
        "opportunity_commitment": {
          "precision": 0.6842,
          "recall": 0.8667,
          "f1": 0.7647,
          "support": 15
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 0.7222,
          "f1": 0.8387,
          "support": 18
        },
        "neutral": {
          "precision": 0.8182,
          "recall": 0.8182,
          "f1": 0.8182,
          "support": 11
        }
      },
      "confusion": {
        "neutral->neutral": 9,
        "neutral->opportunity_commitment": 2,
        "opportunity_commitment->neutral": 2,
        "opportunity_commitment->opportunity_commitment": 13,
        "risk_friction->opportunity_commitment": 1,
        "risk_friction->risk_friction": 12,
        "uncertainty_hedging->opportunity_commitment": 3,
        "uncertainty_hedging->risk_friction": 2,
        "uncertainty_hedging->uncertainty_hedging": 13
      },
      "error_count": 10
    }
  },
  {
    "subset": "human_reviewed",
    "row_count": 12,
    "metrics": {
      "precision": 0.6,
      "recall": 0.6375,
      "f1": 0.5794,
      "per_label": {
        "risk_friction": {
          "precision": 1.0,
          "recall": 0.8,
          "f1": 0.8889,
          "support": 5
        },
        "opportunity_commitment": {
          "precision": 0.4,
          "recall": 1.0,
          "f1": 0.5714,
          "support": 2
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 0.75,
          "f1": 0.8571,
          "support": 4
        },
        "neutral": {
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "support": 1
        }
      },
      "confusion": {
        "neutral->opportunity_commitment": 1,
        "opportunity_commitment->opportunity_commitment": 2,
        "risk_friction->opportunity_commitment": 1,
        "risk_friction->risk_friction": 4,
        "uncertainty_hedging->opportunity_commitment": 1,
        "uncertainty_hedging->uncertainty_hedging": 3
      },
      "error_count": 3
    }
  },
  {
    "subset": "fixture_excluded",
    "row_count": 21,
    "metrics": {
      "precision": 0.6429,
      "recall": 0.6833,
      "f1": 0.646,
      "per_label": {
        "risk_friction": {
          "precision": 1.0,
          "recall": 0.8333,
          "f1": 0.9091,
          "support": 6
        },
        "opportunity_commitment": {
          "precision": 0.5714,
          "recall": 1.0,
          "f1": 0.7273,
          "support": 4
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 0.9,
          "f1": 0.9474,
          "support": 10
        },
        "neutral": {
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "support": 1
        }
      },
      "confusion": {
        "neutral->opportunity_commitment": 1,
        "opportunity_commitment->opportunity_commitment": 4,
        "risk_friction->opportunity_commitment": 1,
        "risk_friction->risk_friction": 5,
        "uncertainty_hedging->opportunity_commitment": 1,
        "uncertainty_hedging->uncertainty_hedging": 9
      },
      "error_count": 3
    }
  },
  {
    "subset": "high_quality",
    "row_count": 12,
    "metrics": {
      "precision": 0.6,
      "recall": 0.6375,
      "f1": 0.5794,
      "per_label": {
        "risk_friction": {
          "precision": 1.0,
          "recall": 0.8,
          "f1": 0.8889,
          "support": 5
        },
        "opportunity_commitment": {
          "precision": 0.4,
          "recall": 1.0,
          "f1": 0.5714,
          "support": 2
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 0.75,
          "f1": 0.8571,
          "support": 4
        },
        "neutral": {
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "support": 1
        }
      },
      "confusion": {
        "neutral->opportunity_commitment": 1,
        "opportunity_commitment->opportunity_commitment": 2,
        "risk_friction->opportunity_commitment": 1,
        "risk_friction->risk_friction": 4,
        "uncertainty_hedging->opportunity_commitment": 1,
        "uncertainty_hedging->uncertainty_hedging": 3
      },
      "error_count": 3
    }
  },
  {
    "subset": "imported_guidance",
    "row_count": 9,
    "metrics": {
      "precision": 0.75,
      "recall": 0.75,
      "f1": 0.75,
      "per_label": {
        "risk_friction": {
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0,
          "support": 1
        },
        "opportunity_commitment": {
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0,
          "support": 2
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0,
          "support": 6
        },
        "neutral": {
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "support": 0
        }
      },
      "confusion": {
        "opportunity_commitment->opportunity_commitment": 2,
        "risk_friction->risk_friction": 1,
        "uncertainty_hedging->uncertainty_hedging": 6
      },
      "error_count": 0
    }
  },
  {
    "subset": "fixture",
    "row_count": 36,
    "metrics": {
      "precision": 0.8365,
      "recall": 0.8045,
      "f1": 0.7954,
      "per_label": {
        "risk_friction": {
          "precision": 0.7778,
          "recall": 1.0,
          "f1": 0.875,
          "support": 7
        },
        "opportunity_commitment": {
          "precision": 0.75,
          "recall": 0.8182,
          "f1": 0.7826,
          "support": 11
        },
        "uncertainty_hedging": {
          "precision": 1.0,
          "recall": 0.5,
          "f1": 0.6667,
          "support": 8
        },
        "neutral": {
          "precision": 0.8182,
          "recall": 0.9,
          "f1": 0.8571,
          "support": 10
        }
      },
      "confusion": {
        "neutral->neutral": 9,
        "neutral->opportunity_commitment": 1,
        "opportunity_commitment->neutral": 2,
        "opportunity_commitment->opportunity_commitment": 9,
        "risk_friction->risk_friction": 7,
        "uncertainty_hedging->opportunity_commitment": 2,
        "uncertainty_hedging->risk_friction": 2,
        "uncertainty_hedging->uncertainty_hedging": 4
      },
      "error_count": 7
    }
  }
]
```
