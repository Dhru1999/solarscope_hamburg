# Learning log: SolarScope Hamburg

My notes while building this project, step by step. What I did, what went wrong,
how I fixed it, and what I learned.

(Written from my code, my code comments and my commits, so I don't forget.)

---

## Step 1: Loading the data into Databricks

**What I did:** uploaded the roof CSV and the district GeoJSON to a Databricks
Volume and read them with Spark.

**Problems:**
- The CSV uses `;` and not `,` as separator, so I had to set `sep=';'`.
- The GeoJSON is one big object (a FeatureCollection), not one row per line.
  Spark needs `option("multiLine", "true")` to read it.
- Then all districts were inside one `features` array. I used `F.explode("features")`
  to get one row per district.

**Learned:** before reading a file, open it and look at how it is built.

---

## Step 2: Bronze table, fixing the column types

**Problem:** all columns came in as text (string), also the numbers.

**What I did:** converted them to numbers in a loop. I used `try_cast` and not
`cast`, because with `try_cast` a bad value becomes `NULL` and the job doesn't crash.

**Problem:** the id column `_fid` had characters that are not numbers.

**Fix:** removed everything that is not a digit with `regexp_replace`, cast it to
int and renamed it to `id`.

**Learned:** `printSchema()` and `show()` first, always. Then fix.

**Note to myself:** I did these fixes *before* saving Bronze. Strictly, Bronze
should be the raw data and the fixes belong in Silver. I'll do it like that next time.

---

## Step 3: Silver table, cleaning

**What I did:**
- The suitability column `eignung` was long German text like
  *"Eignung 1 (geeignet, sehr hohe Einstrahlung)"*. I turned it into numbers with
  `CASE WHEN` and renamed it `suitability_class`.
- Removed class 0 (bad data quality) and class 8 (no building, only ground).
- Found roofs with area over 100,000 m², which is impossible for one roof, so I removed them.
- Dropped `coordinate_reference_system`, because it was always the same value.
- `dropDuplicates()` just to be safe.

**Learned:** print row counts before and after cleaning, so you know how much you removed.

---

## Step 4: Which district is each roof in? (the hardest part for me)

**Problem 1:** roofs and districts don't use the same coordinate system.
Roofs are in metres (EPSG:25832), districts in degrees (WGS84).
You can't compare them like this.

**Fix:** transformed the districts with `pyproj`. Only 104 districts, so that's much
faster than transforming 864k roofs. I needed `always_xy=True`, otherwise
the order of latitude and longitude can get mixed up.

**Problem 2:** checking 864k roofs one by one is too slow.

**Fix:** took the centre point of each roof and used `shapely.STRtree`
(a spatial index), so all points are checked in one go.

**Problem 3:** some roofs had no district after the join. Their centre point was
exactly on a district border.

**Fix:** for those roofs I took the nearest district (max 500 m). Then I checked
again: roofs without district = 0.

**Also needed:** `%pip install shapely pyproj` in the notebook first.

**Learned:** geo data is not "just columns". Always check the coordinate system first.

---

## Step 5: Gold table

Grouped everything by district with SQL: number of roofs, total power,
suitable power (classes 1–3), suitable roofs, PV area. Exported it as a small
CSV (`solar_districts.csv`, 103 rows) for the app.

**Something I didn't expect:** only 53% of the roofs are suitable, but they
have 90% of the power. Big roofs make the difference.

---

## Step 6: First model (v1), and why it was wrong

**What I did:** HistGradientBoosting with a random 80/20 split. I already left out
the output columns like `power` and `pvarea`, because they come from the same
analysis as the label.

**Problem:** I still used `schattena` and `percentmsa`, which are radiation values.
But the suitability class is basically *calculated from* radiation. So the model
could almost read the answer. That's cheating, not learning.

**Second problem:** with a random split, roofs from the same district are in train
and test. Neighbour roofs are very similar, so the score looks better than it is.

**Learned:** for every feature, ask "Would a normal person know this before?"
If not, don't use it.

---

## Step 7: Second model (v2)

**What I changed:**
- only features a homeowner knows: size, direction, tilt, shading, roof type, district
- Random Forest (100 trees, max depth 12)
- split **by district**: every 5th district is only for testing (21 districts)

**Result:** train 694,689 roofs, test 169,669 roofs →
accuracy 0.88, macro F1 0.863.

**Then I checked what the model learned** (feature importance):
shading 59.5%, direction 24.5%, tilt 9.7%, roof type 3.4%, size 2.4%, district 0.3%.
That makes sense physically. District is almost 0, so it really learned roofs
and not neighbourhoods.

**Learned:** don't only look at the score. Look inside the model too.

---

## Step 8: MLflow and Unity Catalog

**Error:** `Registered Model ... not found`, even though the model was registered.

**Why:** MLflow was looking in the old workspace registry, not in Unity Catalog.

**Fix:** one line before loading:
```python
mlflow.set_registry_uri("databricks-uc")
```

**Something new:** when I ran the v2 cell again, it registered a **new version (3)**.
Every registration creates a new version. My app uses version 2 fixed in the
URI, so nothing changed in the app.

**Learned:** always use a fixed model version in the app.

---

## Step 9: Building the Streamlit app

**What I did:** a multipage app. `Home.py` is the start file, and every file in
`pages/` becomes a page in the sidebar automatically (Map, My roof, Insights).

**Small things I learned on the way:**
- `st.set_page_config` must be the **first** Streamlit command.
- `@st.cache_resource`: the model loads once, not on every click.
- Build file paths from `__file__`, so it works from any folder.
- Put a `try/except` around the model and show `st.error`, so the app shows
  a message instead of crashing.
- I kept the old `app.py` as an empty file, so old links don't break.

---

## Step 10: Bug: results disappear when moving the slider

**Problem:** on *My roof*, after clicking "Check my roof", when I moved the
electricity price slider, all results were gone.

**Why:** Streamlit runs the whole script again on every change. The slider was
inside `if st.button(...)`, and on the new run the button is `False` again.

**Fix:** save the prediction and the roof values in `st.session_state` and show
the results outside the button block. Now the savings change live with the
slider and the prediction stays.

**Learned:** a button is only `True` for one run. If something should stay, save it.

---

## Step 11: Git problem with MLflow

**Problem:** the MLflow experiment folder `solar_suitability_model` should not go
into Git. I wrote it in `.gitignore` with a `/` at the end, but that only works for
normal folders, and the experiment is not a normal folder.

**Fix:** removed the trailing slash (commit "Fix .gitignore…").

---

## Step 12: The app said things the notebook didn't show

When I checked my repo, I found mismatches:
- The Home page said, "trained on 864,358 roofs". That's all the data, not the
  training data.
- The Home page called the Bronze table `solar_raw_csv`, but in the notebook it is `solar_raw`.
- The app showed 88% accuracy, but the v2 cell didn't log anything to MLflow.

**Fix:** The v2 cell now logs parameters and metrics to MLflow and registers
the model. The Home page now says 694,689 train / 169,669 test, and the table
name is corrected.

**Learned:** every number in the app needs a place where it comes from.

---

## Step 13: Making the app public (Streamlit Community Cloud)

**Problem:** On Databricks, the app worked, but only for people with access.
On Streamlit Cloud, "My roof" can't load the model because there is no
connection to Unity Catalog.

**Fix:**
- exported the v2 model as a file: `assets/solar_suitability_model.joblib` (11.6 MB)
- checked that it gives the same predictions as the model from Unity Catalog
- in the app: try Unity Catalog first, and if that fails, load the file
- added `streamlit` and `joblib` to `requirements.txt`

Now it's live: https://solarscopehamburg-o97rjf53ukjsbdkgzyzcqe.streamlit.app/

**Learned:** The registry is for managing the model, and a file is for
taking it somewhere else.

---

## Still open/next time

- [ ] Save the notebook with outputs (right now the outputs are not in the repo)
- [ ] Write the exact `scikit-learn` version in `requirements.txt`, so the model file still loads after updates
- [ ] Keep Bronze really raw, and do the type fixes in Silver
- [ ] Look at which class the model mixes up most (confusion matrix for v2)
- [ ] Why do villa districts like Blankenese have so few suitable roofs? Trees? Check shading per district.
- [ ] Rename the notebook (typo:* Ingestion*) and split it into pipeline and model
- [ ] Map with real district shapes instead of bubbles
- [ ] Add the data source links
- [ ] Later: all German states, not only Hamburg
