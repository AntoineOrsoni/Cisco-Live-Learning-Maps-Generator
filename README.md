Generates Cisco Live Amsterdam 2023 Learning Maps based on the [Cisco Live Session Catalog](https://www.ciscolive.com/emea/learn/sessions/session-catalog.html?).

# Colour code in the agenda

Colour code is based on the level of the session.

- Green: Introduction session
- Orange: Intermediate session
- Red: Advanced session
- Blue: General session

# Setup

```
pip install -r requirements.txt
```

## Fixing the Calendar_View library

We encountered a few unexpected behavior with the Calendar_View library. 

You need to edit the `core/calendar_events.py` file.

Line 104 should be: `if i.start_time <= j.start_time < i.end_time \`

![1671006485832](image/README/1671006485832.png)

Line 156 should be: `cell_inner_size: tuple[int, int] = EventDrawHelper.count_cell_inner_size((x1, x2), y)`

![1671006496308](image/README/1671006496308.png)

# Usage

Run the Jupyter Notebook `learning_map_http.ipynb`.
The Learning Maps will be saved in `learning_maps` folder.

# Example

![IPv6 Learning Map](learning_maps/IPv6.png)
