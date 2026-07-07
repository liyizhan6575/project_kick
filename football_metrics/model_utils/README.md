# model_utils

Reusable **trained model weights**, committed so the notebooks' inference demos
run without retraining:

| File | Produced by | Contents |
| :--- | :--- | :--- |
| `xgb_xG_model.pkl` | `xG.ipynb` | `(XGBoost model, feature columns)` |
| `lr_xG_model.pkl`  | `xG.ipynb` | `(imputer + logistic-regression pipeline, feature columns)` |
| `xt_surface.npy`   | `xT.ipynb` | trained Expected Threat value grid |

Regenerate by re-running the corresponding notebook; each writes here on execution.
