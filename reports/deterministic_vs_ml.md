# Deterministic vs ML

This is a benchmark-only comparison. Deterministic Signal Engine output remains canonical.

## Deterministic Metrics

```json
{
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
  }
}
```

## TF-IDF + Logistic Regression Metrics

- status: `completed_cv_benchmark`
- rows: `57`
- cv_splits: `5`
```json
{
  "precision": 0.7332,
  "recall": 0.7328,
  "f1": 0.7327,
  "per_label": {
    "risk_friction": {
      "precision": 0.8462,
      "recall": 0.8462,
      "f1": 0.8462,
      "support": 13
    },
    "opportunity_commitment": {
      "precision": 0.5625,
      "recall": 0.6,
      "f1": 0.5806,
      "support": 15
    },
    "uncertainty_hedging": {
      "precision": 0.7059,
      "recall": 0.6667,
      "f1": 0.6857,
      "support": 18
    },
    "neutral": {
      "precision": 0.8182,
      "recall": 0.8182,
      "f1": 0.8182,
      "support": 11
    }
  }
}
```

## Confusion Matrix Summary

- `neutral`: {'neutral': 9, 'opportunity_commitment': 2, 'risk_friction': 0, 'uncertainty_hedging': 0}
- `opportunity_commitment`: {'neutral': 2, 'opportunity_commitment': 9, 'risk_friction': 0, 'uncertainty_hedging': 4}
- `risk_friction`: {'neutral': 0, 'opportunity_commitment': 1, 'risk_friction': 11, 'uncertainty_hedging': 1}
- `uncertainty_hedging`: {'neutral': 0, 'opportunity_commitment': 4, 'risk_friction': 2, 'uncertainty_hedging': 12}

## Strengths And Tradeoffs

- Deterministic: explainable evidence terms, stable behavior, safe canonical path.
- ML: useful disagreement finder and sanity-check baseline on the current label set.
- Tradeoff: ML explanations are weaker and the dataset is far too small for product claims.

## Disagreement Examples

- `opp_account_named_owners_001` gold=`opportunity_commitment` deterministic=`opportunity_commitment` ml=`neutral` text=will send named owners this afternoon with a renewal review for next Tuesday.
- `opp_account_expand_realistic_001` gold=`opportunity_commitment` deterministic=`opportunity_commitment` ml=`uncertainty_hedging` text=we may still expand analytics seats later this quarter.
- `opp_sales_security_review_path_001` gold=`opportunity_commitment` deterministic=`neutral` ml=`uncertainty_hedging` text=the onboarding looks lighter than what we've seen before.
- `unc_sales_security_review_001` gold=`uncertainty_hedging` deterministic=`uncertainty_hedging` ml=`opportunity_commitment` text=if the security review goes well and the onboarding looks lighter than what we've seen before.
- `guidance_call02_9860ae4d461d` gold=`opportunity_commitment` deterministic=`opportunity_commitment` ml=`uncertainty_hedging` text=Yeah, so our guidance is flat.
- `guidance_call08_864ffeb99f4c` gold=`opportunity_commitment` deterministic=`opportunity_commitment` ml=`uncertainty_hedging` text=As a result, we raised our revenue in earnings for share guides.
- `guidance_call09_42126dfb1bf0` gold=`risk_friction` deterministic=`risk_friction` ml=`uncertainty_hedging` text=that's why we have to just our full year non-gap guidance down for both ebit margin and eps.
