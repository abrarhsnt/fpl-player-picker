# FPL Player Picker
Unofficial, free FPL helper (not affiliated with the Premier League): predicts every player's points for the next gameweek, picks the best XI across formations, lists best-value buys.

## Colab (run from the Drive folder that contains app.py)
```python
from google.colab import drive; drive.mount('/content/drive')
%cd "/content/drive/MyDrive/Research/Specific Topics/fpl-player-picker"
!pip -q install -r requirements.txt
!python build_past.py   # once: downloads past seasons -> data/history_past.csv
!python update.py       # every gameweek: current season + train + predict
```
## Deploy
Push the folder to GitHub (GitHub Desktop), then share.streamlit.io -> app.py. The GitHub Action refreshes data daily.
## New season
Edit `fpl/config.py`, delete `data/history_current.csv`, rerun both scripts.
