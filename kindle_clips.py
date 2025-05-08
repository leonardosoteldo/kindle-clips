from dataclasses import dataclass
import datetime as dt
import re

MONTHS: dict = {
    "january"    : 1,
    "february"   : 2,
    "march"      : 3,
    "april"      : 4,
    "may"        : 5,
    "june"       : 6,
    "july"       : 7,
    "august"     : 8,
    "september"  : 9,
    "october"    : 10,
    "november"   : 11,
    "december"   : 12
}

@dataclass
class Clip:
    source: str
    info: str
    content: str

@dataclass
class Highlight:
    # uuid: ???
    source: str
    page: list[int]
    location: list[int]
    date: dt.date | None
    time: dt.time | None
    content: str

@dataclass
class Report:
    notes_cnt: int
    highlights_cnt: int
    highlights: list[Highlight]

### IO
######################################################################



### PARSING
######################################################################

def parse_clips_file(file: str) -> Report:
    """Parse a given file (a path in the form of a str) into a Report.

    Every kindle clip, as existing in the kindle's 'My Clippings.txt'
    file, consists in:
      - a line with the source's title and author;
      - a line with page, location, date and time (of the clip) information;
      - a blank line;
      - a line with the hightlighted text or annotated commentary and
      - a delimiter line made by repeated equal signs: '=========='

    Every line is read, stripped of the newline character, and stored
    as their correspondent Clip's field (the blank and delimiter lines
    are discarded). Then the Clip is evaluated to check if It's a valid
    highlight, discarding it if It's a note. Finally, the Clip is
    passed to the 'parse_clip()' function and stored as a Highlight in
    a list to be returned as part or the output Report.

    An example of a raw kindle clip as seen in a 'My clippings.txt'
    file:

    > Common LISP: A Gentle Introduction to Symbolic Computation (David S. Touretzky)
    > - Your Highlight on page 46 | Location 694-694 | Added on Sunday, August 27, 2023 1:37:08 PM
    >
    > The length of a list is the number of elements it has
    > ==========

    """

    highlights: list[Highlight] = []
    notes: int = 0
    current_clip: list[str] = []
    cnt: int = 1

    with open(file, mode='r', encoding='UTF-8', newline='\n') as f:
        for line in f:
            if cnt >= 5: # The fifth line of a clip should be a delimiter
                clip = Clip(current_clip[0], current_clip[1], current_clip[3])
                if is_valid_clip(clip):
                    highlights.append(parse_clip(clip))
                    current_clip.clear()
                    cnt = 1
                else:
                    notes += 1
                    current_clip.clear()
                    cnt = 1
            else:
                current_clip.append(line.removesuffix('\n'))
                cnt += 1
        else:
            return Report(notes, len(highlights), highlights)

def parse_clip(clip: Clip) -> Highlight:
    """Parse a Clip and generate a Highlight object.

    See 'parse_clips-file() documentation for more information about
    how Kindle stores the clips and how the parsing is done."""

    return Highlight(clip.source,
                     parse_page_info(clip.info),
                     parse_location_info(clip.info),
                     parse_date_info(clip.info),
                     parse_time_info(clip.info),
                     clip.content)

def is_valid_clip(clip: Clip) -> bool:
    """Check if a given Clip is a valid highlight.

    For now it only checks if the clip is not a kindle note."""
    return "Your Note" not in clip.info

def parse_page_info(string: str) -> list[int]:
    "Parse the page information as given in Clip.info."
    match = re.search(r'pages? ([0-9]+)-([0-9]+)|page ([0-9]+)',
                      string, re.IGNORECASE)
    if match is None:
        return []
    else:
        return [int(page) for page in match.groups() if page is not None]

def parse_location_info(string: str) -> list[int]:
    "Parse the location information as given in Clip.info."
    match = re.search(r'Location ([0-9]+)-([0-9]+)|Location ([0-9]+)',
                    string, re.IGNORECASE)
    if match is None:
        return []
    else:
        return [int(loc) for loc in match.groups() if loc is not None]

def parse_date_info(string: str) -> dt.date | None:
    "Parse the date information as given in Clip.info."
    match = re.search(r'Added on [a-z]+, ([a-z]+) ([0-9]{1,2}), ([0-9]{4})',
                      string, re.IGNORECASE)
    if match is None:
        return None
    else:
        year: int  = int(match.group(3))
        month: int = MONTHS[match.group(1).lower()]
        day: int   = int(match.group(2))
        return dt.date(year, month, day)

def parse_time_info(string: str) -> dt.time | None:
    "Parse the time information as given in Clip.info."
    match = re.search(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}) ([AMP]+)$',
                      string, re.IGNORECASE)
    if match is None:
        return None
    else:
        hour: int     = int(match.group(1))
        minutes: int  = int(match.group(2))
        seconds: int  = int(match.group(3))
        period: str   = match.group(4).upper()

        # Convert from 12h time to 24h time
        # TODO: Kindle uses 12am for noon or midnight?
        if period == 'PM' and hour != 12:
            hour += 12
        elif period  == 'AM' and hour == 12:
            hour -= 12

        return dt.time(hour, minutes, seconds)

### TESTS
######################################################################

highlight_clip: Clip = Clip(
    'Ciudad, urbanización y urbanismo en el siglo XX venezolano (Venezuela siglo XX nº 3) (Spanish Edition) (Almandoz Marte, Arturo)',
    '- Your Highlight on pages 40-45 | Location 542-546 | Added on Thursday, November 17, 2022 12:55:54 PM',
    'La Venezuela que ingresa al siglo XX, asolada...'
)

note_clip: Clip = Clip(
    'Common LISP: A Gentle Introduction to Symbolic Computation (Dover Books on Engineering) (David S. Touretzky)',
    '- Your Note on page 217 | Location 3326 | Added on Friday, September 29, 2023 2:00:29 PM',
    'Recursion en la vida real'
)
def test_is_valid_clip():
    assert is_valid_clip(highlight_clip)
    assert not is_valid_clip(note_clip)

def test_parse_clip():
    highlight = parse_clip(highlight_clip)
    assert highlight.source    == highlight_clip.source
    assert highlight.page      == [40, 45]
    assert highlight.location  == [542, 546]
    assert highlight.date      == dt.date(2022, 11, 17)
    assert highlight.time      == dt.time(12, 55, 54)
    assert highlight.content   == 'La Venezuela que ingresa al siglo XX, asolada...'
    # with pt.raises(RuntimeError):
    #     parse_clip(clip("", "", ""))

def test_parse_clips_file():
    highlights = parse_clips_file('testing_clips.txt').highlights
    assert all(map(lambda h: h.source != note_clip.source, highlights))
    assert len(highlights)         == 4
    assert highlights[0].page      == [40]
    assert highlights[0].location  == [542, 546]
    assert highlights[3].source    == 'Python (Python Documentation Authors)'
    assert highlights[3].content.startswith('To use formatted string literals')
    assert highlights[3].date      == dt.date(2024, 5, 10)
    assert highlights[3].time      == dt.time(18, 45, 50)

    # TODO: This logic should be on its own function
def test_parse_time_info():
    assert parse_time_info('11:59:59 PM') == dt.time(23, 59, 59)
    assert parse_time_info('12:00:00 AM') == dt.time(0, 0, 0)
    assert parse_time_info('12:00:01 AM') == dt.time(0, 0, 1)
    assert parse_time_info('11:59:59 AM') == dt.time(11, 59, 59)
    assert parse_time_info('12:00:00 PM') == dt.time(12, 0, 0)
    assert parse_time_info('12:00:01 PM') == dt.time(12, 0, 1)
