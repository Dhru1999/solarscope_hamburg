# 📘 LEARNING.md
### *The things this project taught me, told as plot twists*
---

## 🗺️ The journey in one picture

```
 RAW DATA ──► CLEAN ──► LOCATE ──► SUMMARISE ──► PREDICT ──► SHOW
    │           │          │           │            │          │
 "it's just  "which    "two maps    "a count    "my model   "a button
  a CSV"     rows are   that don't   and a sum   was too     can erase
             real       agree"       tell        good"       my results"
             roofs?"                 different
                                     stories"
```

---

## 🎬 Plot twist #1: *My model was too good to be honest*

**What I believed:** more features → better model. v1 used every
reasonable-looking column, including the radiation values `schattena` and `percentmsa`.

**What I realised:** the suitability class (*Eignung*) is basically **calculated
from radiation**. Giving the model radiation is like letting a student revise
with the answer sheet on the desk. The score looks great, but nothing is learned.

**What I do now** (model v2, notebook cell 25): only features a homeowner knows
*before* a solar study: size, direction, tilt, shading, roof type, district.

**🔑 My rule from now on:**
> *"Would I actually have this value at the moment I need the prediction?"*
> If not, it's leakage, no matter how much it helps the score.

---

## 🎬 Plot twist #2: *A random split let my model recognise neighbourhoods*

Roofs in the same district are siblings: same era, same streets, same trees.
With a random 80/20 split, the test roofs had "siblings" in the training set.

**v2 holds out whole districts** (every 5th, alphabetically: 21 districts). Now the
test asks the honest question: *"Does this work in a part of the city you've never seen?"*

**🔑 Lesson:** The test split should copy how the model will be used in real life.
A homeowner from a new area doesn't care how well I did on their neighbours.

---

## 🎬 Plot twist #3: *Two maps of the same city didn't agree*

| | Roofs | Districts |
| --- | --- | --- |
| System | EPSG:25832 | WGS84 (EPSG:4326) |
| Unit | metres | degrees |

Until both use the same system, "is this roof inside this district?" is meaningless.

**What I did** (notebook cell 16):
- reprojected the **104 districts** instead of **864k roofs**: same result, far
  less work
- used `always_xy=True` so pyproj doesn't silently swap latitude and longitude
- built a `shapely.STRtree` so the matching happens in one vectorised query,
  not 864k loops

**The edge case:** a roof whose centre sits *exactly on a border* belongs to no
district. Fix: assign the **nearest district within 500 m**, then **check** that every
roof has one (`roofs without district` is printed).

**A simplification I chose on purpose:** I matched each roof's *centre point*, so a
roof crossing a border counts for one district only.

---

## 🎬 Plot twist #4: *Half the roofs, 90% of the power*

When I aggregated the Gold table, two numbers didn't fit my intuition:

- **53%** of roof faces are suitable
- they hold **90%** of the potential peak power

And one average roof face in **Altenwerder** (port) has about **16×** the
potential of one in **Blankenese**.

**🔑 Lesson:** *counts* and *sums* tell different stories. That's why the Insights
page shows both a **share** of suitable roofs and **total** power. Neither one
alone gives the full picture.

---

## 🎬 Plot twist #5: *My "raw" layer isn't fully raw*

The medallion idea is simple:

| 🥉 Bronze | 🥈 Silver | 🥇 Gold |
| --- | --- | --- |
| keep everything as delivered | clean, trusted rows | answers, one row per district |

**The idea behind it:** if I find a cleaning mistake later, I rebuild Silver and
Gold. I never re-download.

**Honest review of my own code:** I cast types and cleaned the id *before*
saving Bronze. In a strict setup, Bronze stays untouched and casting happens in Silver.
It works, but next time I'll keep Bronze pure.

---

## 🎬 Plot twist #6: *A button can erase your results*

On the **My roof** page, the electricity-price slider sits *inside*
`if st.button(...)`. Streamlit reruns the whole script on every widget change, and
on that rerun the button is `False` again. Move the slider and the results vanish.

**🔑 Lesson:** in Streamlit, a button is a *moment*, not a *state*. To keep
results, store them in `st.session_state`, or put the dependent widgets outside
the button block.

*(Found while reviewing my own code; not fixed yet. See the to-do list.)*

---

## 🧰 Small things that saved me time

| Trick | Where | Why it matters |
| --- | --- | --- |
| `try_cast` instead of `cast` | cell 5 | bad values become `NULL` instead of crashing the job |
| `mlflow.set_registry_uri("databricks-uc")` | `2_My_Roof.py` | without it MLflow says *"model not found"*, even though the model exists in Unity Catalog |
| `@st.cache_resource` | `2_My_Roof.py` | load the model once, not on every click |
| paths built from `__file__` | all pages | the app runs from any folder |
| `st.set_page_config` first | `Home.py` | it must be the first Streamlit command |
| small CSV export in `assets/` | Map, Insights | 2 of 3 pages work without Databricks |
| `try/except` + `st.error` | `2_My_Roof.py` | a clear message instead of a crash |
| no trailing slash in `.gitignore` | last commit | the MLflow experiment isn't a plain folder, and a trailing slash only matches directories |
| keep `app.py` as a stub | `app.py` | moving to a multipage app didn't break old links |

## ❓ Things I don't know yet (and want to find out)

- **Why** are the villa districts (Blankenese, Rissen, Nienstedten) so low on suitable
  roofs? Trees? Roof shapes? → compare the average `schatten` and `slope` per district.
- **Why** do port districts have such huge roofs? → check roof area distributions.
- **Which suitability class** does my model confuse most? → per-class report and
  confusion matrix for v2.
- **Does it travel?** Would a model trained on Hamburg work for another German city?

---

## ✅ To-do list (from reviewing my own work)

- [ ] Commit the cell that logs and registers **model v2** and save its metrics
- [ ] Fix the Home page wording: training uses the district split, not all 864,358 roofs
- [ ] Align table names (`solar_raw_csv` on the Home page vs `solar_raw` in the notebook)
- [ ] Move the price slider out of the button block/use `st.session_state.`
- [ ] Add `streamlit` to `requirements.txt` for running outside Databricks
- [ ] Rename the notebook (*Ingetion* → *Ingestion*) and split it in two
- [ ] Replace the bubble map with a filled choropleth from the district GeoJSON
- [ ] Add data source links and licence to the README
- [ ] 🇩🇪 Extend from Hamburg to all German states
