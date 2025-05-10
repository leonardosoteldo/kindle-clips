from dataclasses import dataclass
from datetime import date, time
from re import search, IGNORECASE
import argparse

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
class RawClip:
    source: str
    info: str
    blank: str
    content: str
    delimiter: str

@dataclass
class Clip:
    type: str
    source: str
    page: list[int]
    location: list[int]
    date: date | None
    time: time | None
    content: str

@dataclass
class Extraction:
    highlights: list[Clip]
    notes: list[Clip]

### CLIPS PARSING
######################################################################

# TODO: add functionality for notes also.
# TODO: add basic sorting for output

def parse_rawclips_file(file: str) -> Extraction:
    """Parse a given file (a path in the form of a str) into a Extraction.

    Every kindle clip, as existing in the kindle's 'My Clippings.txt'
    file, consists in:
      - a line with the source's title and author;
      - a line with page, location, date and time (of the clip) information;
      - a blank line;
      - a line with the hightlighted text or annotated commentary and
      - a delimiter line made by repeated equal signs: '=========='

    Every line is read, stripped of the newline character, and stored
    as their correspondent RawClip's field. The RawClip is evaluated
    to check if It's a highlight or a note. Finally, the RawClip is
    passed to the 'parse_rawclip()' function and stored as a Clip in a
    list to be returned as part or the output Extraction.

    An example of a raw kindle clip as seen in a 'My clippings.txt'
    file:

    > Common LISP: A Gentle Introduction to Symbolic Computation (David S. Touretzky)
    > - Your Highlight on page 46 | Location 694-694 | Added on Sunday, August 27, 2023 1:37:08 PM
    >
    > The length of a list is the number of elements it has
    > ==========

    """

    highlights: list[Clip]  = []
    notes: list[Clip]       = []
    current_clip: list[str] = []
    cnt: int                = 1

    with open(file, mode='r', encoding='UTF-8', newline='\n') as f:

        for line in f:

            # The fifth line of a clip should be a delimiter
            if cnt >= 5:
                cnt = 1
                clip = parse_rawclip(RawClip(current_clip[0],
                                             current_clip[1],
                                             current_clip[2],
                                             current_clip[3],
                                             line.removesuffix('\n')))

                if clip.type == 'highlight':
                    highlights.append(clip)
                    current_clip.clear()
                elif clip.type == 'note':
                    notes.append(clip)
                    current_clip.clear()
                else:
                    raise RuntimeError

            else:
                current_clip.append(line.removesuffix('\n'))
                cnt += 1

        else:
            return Extraction(highlights, notes)

def parse_rawclip(rawclip: RawClip) -> Clip:
    """Parse a RawClip and generate a Clip object.

    See 'parse_clips-file() documentation for more information about
    how Kindle stores the clips and how the parsing is done."""
    return Clip(get_rawclip_type(rawclip),
                rawclip.source,
                parse_page_info(rawclip.info),
                parse_location_info(rawclip.info),
                parse_date_info(rawclip.info),
                parse_time_info(rawclip.info),
                rawclip.content)

def get_rawclip_type(rclip: RawClip) -> str:
    "Checks rclip type and return 'highlight' or 'note' string."
    if  rclip.info.startswith('- Your Highlight'):
        return 'highlight'
    elif rclip.info.startswith('- Your Note'):
        return 'note'
    else:
        raise RuntimeError('Your Kindle clips file looks weird. Couldn\'t parse it')

def parse_page_info(string: str) -> list[int]:
    "Parse the page information as given in Clip.info."
    match = search(r'pages? ([0-9]+)-([0-9]+)|page ([0-9]+)',
                      string, IGNORECASE)
    if match is None:
        return []
    else:
        return [int(page) for page in match.groups() if page is not None]

def parse_location_info(string: str) -> list[int]:
    "Parse the location information as given in Clip.info."
    match = search(r'Location ([0-9]+)-([0-9]+)|Location ([0-9]+)',
                    string, IGNORECASE)
    if match is None:
        return []
    else:
        return [int(loc) for loc in match.groups() if loc is not None]

def parse_date_info(string: str) -> date | None:
    "Parse the date information as given in Clip.info."
    match = search(r'Added on [a-z]+, ([a-z]+) ([0-9]{1,2}), ([0-9]{4})',
                      string, IGNORECASE)
    if match is None:
        return None
    else:
        year: int  = int(match.group(3))
        month: int = MONTHS[match.group(1).lower()]
        day: int   = int(match.group(2))
        return date(year, month, day)

def parse_time_info(string: str) -> time | None:
    "Parse the time information as given in Clip.info."
    match = search(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}) ([AMP]+)$',
                      string, IGNORECASE)
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

        return time(hour, minutes, seconds)

### IO
######################################################################

def text_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into a pretty text format."""
    return 'text formatter not implemented'

def org_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into a pretty org-mode format."""
    return 'org formatter not implemented'

def json_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into json format."""
    return 'json formatter not implemented'

parser = argparse.ArgumentParser(
    prog='kindle-highlights',
    description='''Convert Kindle highlights into formatted text,
    org-mode or JSON entries.''',
    epilog='More info at https://github.com/leonardosoteldo/kindle-highlights')

parser.add_argument('file', type=str,
                    help='File that contains the Kindle highlights.')

parser.add_argument('-o', '--output-file', type=str, default=None,
                    help='''Define the output file of the program.
                    stdout is used if none given.''')

parser.add_argument('-f', '--format', type=str, choices=['text', 'org', 'json'],
                    default='text', help="""Define the format of the
                    output. Could be 'text', 'org' or 'json'. Defaults
                    to 'text'""")

type_of_clips = parser.add_mutually_exclusive_group()

type_of_clips.add_argument('-H', '--highlights', action='store_true',
                           help='''If used, the only clips extracted
                           are highlights. The default is all clips.''')

type_of_clips.add_argument('-n', '--notes', action='store_true',
                           help='''If used, the only clips extracted
                           are notes. The default is all clips.''')

parser.add_argument('-q', '--quiet', action='store_true',
                    help="Dont't print any message.")

args = parser.parse_args()

if __name__ == '__main__':

    match args.format:
        case 'text':
            formatter_func = text_formatter
        case 'org':
            formatter_func = org_formatter
        case 'json':
            formatter_func = json_formatter
        case _:
            raise RuntimeError

    extraction: Extraction = parse_rawclips_file(args.file)

    if args.notes:
        if not args.quiet:
            print(f"Processing '{args.file}'.")
            print(f"Found {len(extraction.notes)} notes.")

        results = formatter_func(extraction.notes)

    elif args.highlights:
        if not args.quiet:
            print(f"Processing '{args.file}'.")
            print(f"Found {len(extraction.highlights)} highlights.")

        results = formatter_func(extraction.highlights)

    else: # notes and highlights
        if not args.quiet:
            print(f"Processing '{args.file}'.")
            print(f"Found {len(extraction.notes)} notes.")
            print(f"Found {len(extraction.highlights)} highlights.")
        results = formatter_func(extraction.notes + extraction.highlights)

    if args.output_file is None:
        print(results)
    else:
        with open(args.output_file, mode='w', encoding='utf-8') as file:
            file.write(results)

### TESTS
######################################################################

import pytest

highlight_rawclip: RawClip = RawClip(
    'Ciudad, urbanización y urbanismo en el siglo XX venezolano (Venezuela siglo XX nº 3) (Spanish Edition) (Almandoz Marte, Arturo)',
    '- Your Highlight on pages 40-45 | Location 542-546 | Added on Thursday, November 17, 2022 12:55:54 PM',
    '',
    'La Venezuela que ingresa al siglo XX, asolada...',
    '==========')

note_rawclip: RawClip = RawClip(
    'Common LISP: A Gentle Introduction to Symbolic Computation (Dover Books on Engineering) (David S. Touretzky)',
    '- Your Note on page 217 | Location 3326 | Added on Friday, September 29, 2023 2:00:29 PM',
    '',
    'Recursion en la vida real',
    '==========')

corrupted_rawclip: RawClip = RawClip(
    'Common LISP: A Gentle Introduction to Symbolic Computation (Dover Books on Engineering) (David S. Touretzky)',
    '- Your Clip on page 217 | Location 3326 | Added on Friday, September 29, 2023 2:00:29 PM',
    '',
    'Recursion en la vida real',
    '==========')

def test_get_rawclip_type():
    assert get_rawclip_type(highlight_rawclip) == 'highlight'
    assert get_rawclip_type(note_rawclip) == 'note'
    with pytest.raises(RuntimeError):
        get_rawclip_type(corrupted_rawclip)

def test_parse_rawclip():
    highlight = parse_rawclip(highlight_rawclip)
    assert highlight.source    == highlight_rawclip.source
    assert highlight.page      == [40, 45]
    assert highlight.location  == [542, 546]
    assert highlight.date      == date(2022, 11, 17)
    assert highlight.time      == time(12, 55, 54)
    assert highlight.content   == 'La Venezuela que ingresa al siglo XX, asolada...'

def test_parse_rawclips_file():
    testing_clips = parse_rawclips_file('testing_clips.txt')
    # Tests for highlights extraction
    highlights = testing_clips.highlights
    assert all(map(lambda c: c.source != note_rawclip.source, highlights))
    assert len(highlights)         == 4
    assert highlights[0].page      == [40]
    assert highlights[0].location  == [542, 546]
    assert highlights[3].source    == 'Python (Python Documentation Authors)'
    assert highlights[3].content.startswith('To use formatted string literals')
    assert highlights[3].date      == date(2024, 5, 10)
    assert highlights[3].time      == time(18, 45, 50)
    # Tests for notes extraction
    notes = testing_clips.notes
    assert all(map(lambda c: c.source != highlight_rawclip.source, notes))
    assert len(notes)         == 3
    assert notes[0].page      == [217]
    assert notes[0].location  == [3326]
    assert notes[0].source.startswith('Common LISP:')
    assert notes[0].content.startswith('Recursion en la vida real')

def test_parse_time_info():
    assert parse_time_info('11:59:59 PM') == time(23, 59, 59)
    assert parse_time_info('12:00:00 AM') == time(0, 0, 0)
    assert parse_time_info('12:00:01 AM') == time(0, 0, 1)
    assert parse_time_info('11:59:59 AM') == time(11, 59, 59)
    assert parse_time_info('12:00:00 PM') == time(12, 0, 0)
    assert parse_time_info('12:00:01 PM') == time(12, 0, 1)
