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
class Highlight:
    # uuid: ???
    source: Source | str
    page: list[int]
    location: list[int]
    date: dt.date
    time: dt.time
    content: str

def parse_clips_file(file: str) -> list[Highlight]:
    """Parse a given file (a path in the form of a str) into a list of Highlights.

    Every kindle clip, as existing in the kindle's 'My Clippings.txt' file, consists in:
      - a line with the source's title and author;
      - a line with page, location, date and time (of the clip) information;
      - a line with the hightlighted text or annotated commentary;
      - and a delimiter line made by repeated equal signs: '=========='

    Every line is read and stored as a separate string in a list (the delimiter line is discarded), the second line is evaluated to check if the clip is a note and discard it if True. Then the list of strings (clip) is passed to the 'parse_clip()' function, and its output (a Highlight) is stored in a list of Highlights to be returned as output.
    """
    return []

def parse_clip(clip: list[str]) -> Highlight:
    """Parse a kindle clip (a list of three strings) and generate a Highlight object"""

    source: str = clip[0]
    metadata: str = clip[1]
    content: str = clip[2]

    m_pages = re.search(r'pages? ([0-9]+)-([0-9]+)|page ([0-9]+)', metadata, re.IGNORECASE)
    m_loc   = re.search(r'Location ([0-9]+)-([0-9]+)|Location ([0-9]+)', metadata, re.IGNORECASE)
    m_date  = re.search(r'Added on [a-z]+, ([a-z]+) ([0-9]{1,2}), ([0-9]{4})', metadata, re.IGNORECASE)
    m_time  = re.search(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}) ([AMP]+)$', metadata, re.IGNORECASE)

    pages: list[int] = list(filter(lambda e: e is not None, m_pages.groups()))
    loc: list[int] = list(filter(lambda e: e is not None, m_loc.groups()))
    date: dt.date = dt.date(int(m_date.group(3)),
                            MONTHS[m_date.group(1).lower()],
                            int(m_date.group(2)))
    time: dt.time = dt.time(int(m_time.group(1)),
                            int(m_time.group(2)),
                            int(m_time.group(3)))

    return Highlight(source,
                     list(map(lambda e: int(e), pages)),
                     list(map(lambda e: int(e), loc)),
                     date,
                     time,
                     content)

def is_valid_clip(clip: list[str]) -> bool:
    """Check if a given kindle clip (a list of three strings) is a valid kindle highlight.

    This seeks both for noise in the clips file (very rare) and if the given clip is a note instead of a highlight, checking the second string of the input list"""
    return "Your Note" not in clip[1]

### TESTS
######################################################################

highlight_clip: list[str] = [
    'Ciudad, urbanización y urbanismo en el siglo XX venezolano (Venezuela siglo XX nº 3) (Spanish Edition) (Almandoz Marte, Arturo)',
    '- Your Highlight on pages 40-45 | Location 542-546 | Added on Thursday, November 17, 2022 12:55:54 PM',
    'La Venezuela que ingresa al siglo XX, asolada...'
]
note_clip: list[str] = [
    'Common LISP: A Gentle Introduction to Symbolic Computation (Dover Books on Engineering) (David S. Touretzky)',
    '- Your Note on page 217 | Location 3326 | Added on Friday, September 29, 2023 2:00:29 PM',
    'Recursion en la vida real'
]
def test_is_valid_clip():
    assert is_valid_clip(highlight_clip)
    assert not is_valid_clip(note_clip)

def test_parse_clip():
    highlight = parse_clip(highlight_clip)
    assert highlight.source    == highlight_clip[0]
    assert highlight.page      == [40, 45]
    assert highlight.location  == [542, 546]
    assert highlight.date      == dt.date(2022, 11, 17)
    assert highlight.time      == dt.time(12, 55, 54)
    assert highlight.content   == 'La Venezuela que ingresa al siglo XX, asolada...'

def test_parse_clips_file():
    highlights = parse_clips_file('testing_clips.txt')
    assert len(highlights) == 4
    assert all(map(lambda h: h.source != note_clip[0], highlights))
    assert highlights[0].page == [40]
    assert highlights[0].location == [542, 546]
    assert highlights[3].source == 'Python (Python Documentation Authors)'
    assert highlights[3].date == dt.date(2024, 5, 10)
    assert highlights[3].date == dt.time(18, 45, 50)
