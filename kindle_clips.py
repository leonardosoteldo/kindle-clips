from dataclasses import dataclass
import datetime as dt
import re
import pytest as pt

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

# TODO: implementation of different sources (periodic, etc.)
@dataclass
class Source:
    # uuid: ???
    author: str
    title: str
    place: str
    publisher: str
    edition: int # edition number
    year: int
    pp: int # number of total pages

@dataclass
class Clip:
    source: str
    info: str
    content: str

@dataclass
class Highlight:
    # uuid: ???
    source: Source | str
    page: list[int]
    location: list[int]
    date: dt.date | None
    time: dt.time | None
    content: str

def parse_clips_file(file: str) -> list[Highlight]:
    """Parse a given file (a path in the form of a str) into a list of Highlights.

    Every kindle clip, as existing in the kindle's 'My Clippings.txt'
    file, consists in:
      - a line with the source's title and author;
      - a line with page, location, date and time (of the clip) information;
      - a line with the hightlighted text or annotated commentary;
      - and a delimiter line made by repeated equal signs: '=========='

    Every line is read and stored as a separate string in a list (the
    delimiter line is discarded), the second line is evaluated to
    check if the clip is a note and discard it if True. Then the list
    of strings (clip) is passed to the 'parse_clip()' function, and
    its output (a Highlight) is stored in a list of Highlights to be
    returned as output."""

    return []

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
    pages = re.search(r'pages? ([0-9]+)-([0-9]+)|page ([0-9]+)',
                      string, re.IGNORECASE)
    if pages is None:
        return []
    else:
        return [int(p) for p in pages.groups() if p is not None]

def parse_location_info(string: str) -> list[int]:
    "Parse the location information as given in Clip.info."
    loc = re.search(r'Location ([0-9]+)-([0-9]+)|Location ([0-9]+)',
                    string, re.IGNORECASE)
    if loc is None:
        return []
    else:
        return [int(l) for l in loc.groups() if l is not None]

def parse_date_info(string: str) -> dt.date | None:
    "Parse the date information as given in Clip.info."
    date  = re.search(r'Added on [a-z]+, ([a-z]+) ([0-9]{1,2}), ([0-9]{4})',
                      string, re.IGNORECASE)
    if date is None:
        return None
    else:
        return dt.date(int(date.group(3)),
                       MONTHS[date.group(1).lower()],
                       int(date.group(2)))

def parse_time_info(string: str) -> dt.time | None:
    "Parse the time information as given in Clip.info."
    time  = re.search(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}) ([AMP]+)$',
                      string, re.IGNORECASE)
    if time is None:
        return None
    else:
        return dt.time(int(time.group(1)),
                       int(time.group(2)),
                       int(time.group(3)))

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
    highlights = parse_clips_file('testing_clips.txt')
    assert all(map(lambda h: h.source != note_clip.source, highlights))
    assert len(highlights)         == 4
    assert highlights[0].page      == [40]
    assert highlights[0].location  == [542, 546]
    assert highlights[3].source    == 'Python (Python Documentation Authors)'
    assert highlights[3].date      == dt.date(2024, 5, 10)
    assert highlights[3].date      == dt.time(18, 45, 50)
