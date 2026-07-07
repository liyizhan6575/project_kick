![Banner](repo_media/repo_banner.png)

# README

`Project KICK` is an open repository focused on **football (soccer) analytics and applied science**, with an emphasis on clear methodology and reproducible analysis.

The goal of this project is to explore how ideas from **data science, computer science, mathematics, and physics** can be used to better understand football.

To install the Python dependencies used by the notebooks and animation modules, run `pip install -r requirements.txt`.

## 1. Repository Structure

### 1.1 football_metrics

This module contains implementations and experiments around football analytics metrics that aim to quantify tactical structure, player contribution, and contextual game value. Each metric is a self-contained notebook; shared code lives in [`data_loaders/`](./football_metrics/data_loaders) (Opta / Hawk-Eye event & tracking processors), [`visualization_helper/`](./football_metrics/visualization_helper) (plotting helpers), and [`model_utils/`](./football_metrics/model_utils) (reusable trained weights).

| Name | File Link | Data Input | Status |
| :--- | :--- | :--- | :--- | 
| Expected Goals (xG) | [`xG.ipynb`](./football_metrics/xG.ipynb) | Event | 🟢 Demo Available |
| Expected Threat (xT) | [`xT.ipynb`](./football_metrics/xT.ipynb) | Event | 🟢 Demo Available |
| Pitch Control | [`pitch_control.ipynb`](./football_metrics/pitch_control.ipynb) | Tracking | 🟢 Demo Available |
| Passing Network | [`passing_network.ipynb`](./football_metrics/passing_network.ipynb) | Event | 🟢 Demo Available |
| Physical Analysis | [`physical_analysis.ipynb`](./football_metrics/physical_analysis.ipynb) | Tracking | 🟢 Demo Available |
| Passes per Defensive Action (PPDA) | [`ppda.ipynb`](./football_metrics/ppda.ipynb) | Event | 🟢 Demo Available |
| Set-Piece Analysis | N/A | Event | 🔴 Developing... | 
| Visual Occupancy | N/A | Tracking | 🔴 Developing... |
| Expected Possession Value (EPV) | N/A | Event + Tracking | 🔴 Developing... |
| On-Ball Value (OBV) | N/A | Event + Tracking | 🔴 Developing... |


### 1.2 football_animations

This module contains [Manim](https://www.manim.community/)-based animation utilities: a pitch-drawing primitive ([`pitch_utils.py`](./football_animations/pitch_utils.py)), Voronoi pitch-control helpers ([`voronoi.py`](./football_animations/voronoi.py)), and a 3D metric surface ([`metric_surface.py`](./football_animations/metric_surface.py)). A minimal runnable scene is provided in [`example_scene.py`](./football_animations/example_scene.py).

| **Metric Surface** | **Voronoi Pitch Control** |
| :---: | :---: |
| ![Metric Surface Animation](repo_media/metric_surface_example.gif) | ![Voronoi Animation](repo_media/voronoi_example.gif) |

### 1.3 football_simulations

| Name | Approach | Status |
| :--- | :--- | :--- |
| Football RL Environment | JAX | 🔴 Developing... |

This module will contain simulation and control: reinforcement learning (RL) environments that allow agents to learn football behaviors from reward signals and environment dynamics. An earlier Unity (ML-Agents) prototype has been retired; the environment is being rebuilt in **JAX** and will be published here when ready.

## 2. Sources and attribution

This project builds on a combination of **open datasets** and, in some cases, **data accessed under non-disclosure agreements (NDA)**. Only analyses and results that are permitted for public release are included in this repository.

The methodologies used throughout the project vary in origin. Some components are based on established academic papers or prior work in the football analytics community, others are original contributions, and many are the result of combining existing ideas with new modeling or implementation choices.

Attribution is treated as an ongoing process. As the project evolves, references and credits will be continuously updated to acknowledge the original sources and contributors that inform this work.

### 2.1 Data Sources

| Source Name | Data Type | Access Level | Attribution / Link |
| :--- | :--- | :--- | :--- |
| Statsbomb Open Data | Event | Public | [Github](https://github.com/statsbomb/open-data) |
| SONY Hawkeye Data | Tracking | NDA | [Official Website](https://www.hawkeyeinnovations.com/data) |
| Opta Data Feed | Event | NDA | [Documentation](https://documentation.statsperform.com/) | 


### 2.2 Academic Foundations

| Metric / Model | Original Paper / Author | Link / Citation |
| :--- | :--- | :--- | 
| Expected Threat (xT) | Karun Singh | [Introducing Expected Threat (xT)](https://karun.in/blog/expected-threat.html) |
| Expected Threat (xT) — implementation basis | Tom Decroos et al., `socceraction` library | [Github](https://github.com/ML-KULeuven/socceraction) |
| Pitch Control | Javier Fernandez & Luke Bornn | [Wide Open Spaces: A statistical technique for measuring space creation in professional soccer](https://www.lukebornn.com/papers/fernandez_ssac_2018.pdf) |
| Tactical Run | Sam Gregory | [Ready Player Run: Off-ball run identification and classification](https://static.capabiliaserver.com/frontend/clients/barca/wp_prod/wp-content/uploads/2020/01/ed15d067-ready-player-run-barcelona-paper-sam-gregory.pdf) | 

## 3. Acknowledgments
Special thanks to the following organizations for their support through data access and technical guidance:
- **Baidu AI Cloud** 
- **Bilibili** 
- **Statsperform Opta**