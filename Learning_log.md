# Learning log

## 2026-11-23 - Where the repo and the app didn't match (and how each was fixed)

I wrote the mismatches down instead of hiding them. Fixes below are committed to the repo.

1. **The 88% accuracy number only existed in the app's Home page.**
   The notebook's model-v2 cell trained the Random Forest but never logged it to
   MLflow or registered it - its results were not saved anywhere in the repo.
   *Fix:* the v2 cell now logs the run to MLflow and registers the model in Unity
   Catalog, and it has been executed - its saved outputs show the 694,689 / 169,669
   district split, 0.88 accuracy and 0.863 macro F1. Registered as version 3
   (version 2, registered earlier from the identical deterministic training, is
   what the app serves).
2. **"Trained on 864,358 roof faces" was wrong.** That is the whole cleaned
   dataset; every 5th district was held out for testing, so the model actually
   trained on **694,689** roofs (169,669 held out).
   *Fix:* Home.py now states both numbers.
3. **The Home page called the Bronze table `solar_raw_csv`,** but the notebook
   saves it as `solar_raw`. *Fix:* Home.py now uses the real name.
4. **Moving the electricity-price slider deleted the "My roof" results** until
   the button was clicked again - the results were rendered inside the
   `if st.button(...)` block, which is False on every rerun triggered by a slider.
   *Fix:* the prediction and the roof inputs are now stored in `st.session_state`
   and rendered outside the button block, so the savings update live when the
   price changes.

## Lessons

- Streamlit reruns the whole script on every widget change - anything rendered
  inside an `if st.button():` block disappears on the next rerun. Persist results
  in `st.session_state` and render them unconditionally.
- A number shown in an app should be traceable to a saved artifact (notebook
  output, MLflow run). Otherwise it is just a claim.
- Match names in prose to what the code actually creates (table names, versions).
