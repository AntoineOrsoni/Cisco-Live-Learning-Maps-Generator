Generates Cisco Live Amsterdam 2023 Learning Maps based on the [Cisco Live Session Catalog](https://www.ciscolive.com/emea/learn/sessions/session-catalog.html?).

You can find all generated Learning Maps in `learning_maps` folder. Each sub-folder is a Learning Map category.

You can find a PDF file for each Learning Map category in `learning_maps/_PDF`. The PDF file has a calendar view for each Learning Map.

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

We encountered a few unexpected behavior with the Calendar_View library. Kudos to **Romain Cyrille** for helping me fix the `calendar_view` library.

You need to edit the `core/calendar_events.py` file.

Line 104 should be: `if i.start_time <= j.start_time < i.end_time \`

![line_104 edit](Code_edits/line_104.jpg)

Line 156 should be: `cell_inner_size: tuple[int, int] = EventDrawHelper.count_cell_inner_size((x1, x2), y)`

![line_156 edit](Code_edits/line_156.jpg)

# Usage

Run the python file `learning_maps.py`. The Learning Maps will be saved in `learning_maps` folder.

Once the calendar view images have been generated, you can create an associated PDF for each Learning Map category. Run the `pdf_generator.ipynb` to do so.

# Example

![IPv6 Learning Map](learning_maps/Networking/IPv6.png)
