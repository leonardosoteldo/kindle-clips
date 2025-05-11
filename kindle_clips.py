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
    line_cnt: int = 0
    cnt: int                = 1

    with open(file, mode='r', encoding='UTF-8', newline='\n') as f:

        for line in f:

            # The fifth line of a clip should be a delimiter. Collect
            # the fivelines, create a RawClip and parse it into a Clip.
            if cnt >= 5:
                rclip = RawClip(current_clip[0],
                                current_clip[1],
                                current_clip[2],
                                current_clip[3],
                                line.removesuffix('\n'))
                try:
                    clip = parse_rawclip(rclip)

                # If parsing returns an error, report it to stdout and
                # continue the file loop.
                except RuntimeError:
                    print_rawclip_parsing_error(rclip, line_cnt)

                    # Clear the lines collector and update counters,
                    # then continue with the next loop iteration
                    current_clip.clear()
                    cnt = 1
                    line_cnt += 1

                    continue

                else:

                    # Collect the clip into the corresponding list
                    match clip.type:
                        case 'highlight':
                            highlights.append(clip)
                        case 'note':
                            notes.append(clip)
                        case 'bookmark':
                            # bookmarks.append(clip)
                            pass
                        case _:
                            raise RuntimeError

                    # Clear the lines collector and update counters
                    current_clip.clear()
                    cnt = 1
                    line_cnt += 1

            else:
                # Collect the lines
                current_clip.append(line.removesuffix('\n'))
                line_cnt += 1
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
        raise RuntimeError("Your Kindle clips file looks weird. Couldn't parse it")

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

### OUTPUT FORMATTING AND MESSASGING
######################################################################

def format_clips(clips: list[Clip], format: str) -> str:
    "Return a string with given Clips properly formatted."

    match format:
        case 'text':
            return text_formatter(clips)
        case 'org':
            return org_formatter(clips)
        case 'json':
            return json_formatter(clips)
        case _:
            raise ValueError('Given format is not defined.')

def text_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into a pretty text format."""

    columns: int = 70
    delimiter: str = '-' * columns + '\n'
    result: list[str] = []

    for clip in clips:

        c = ''.join([f"Source: {clip.source}\n",
                     f"Page: {pages_and_loc_to_str(clip.page)}\n",
                     f"Location: {pages_and_loc_to_str(clip.location)}\n",
                     f"Creation: {str(clip.date)} | {str(clip.time)}\n",
                     f"{clip.type.capitalize()}:\n\n{clip.content}\n",
                     delimiter])

        result.append(c)

    return delimiter + ''.join(result)

def org_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into a pretty org-mode format."""
    return 'org formatter not implemented'

def json_formatter(clips: list[Clip]) -> str:
    """Process a list of clips into json format."""
    return 'json formatter not implemented'

def pages_and_loc_to_str(pp: list[int] | None) -> str:
    "Convert pages and locations into a pretty string."

    if pp is None:
        return 'no data'

    else:
        pp_len: int = len(pp)

        if pp_len == 0:
            return 'no data'
        elif pp_len == 1:
            return str(pp[0])
        elif pp_len == 2:
            return str(pp[0]) + '-' + str(pp[1])
        else:
            return ''.join(str(i) + ', ' for i in pp).removesuffix(', ')

def print_rawclip_parsing_error(rclip: RawClip, line_num: int) -> None:
    "Print message about error while parsing a RawClip."
    print("Got an error while processing your Kindle clips file.")
    print(f"The clip ending at line {line_num} couldn't be parsed:")
    print(f'    > {rclip.source}')
    print(f'ERR > {rclip.info}')
    print(f"    > {rclip.blank}")
    print(f'    > {rclip.content}')

    return

def print_extraction_messages(is_quiet: bool, extraction: Extraction,
                              types: list[str]) -> None:
    "Print information messages of the extracted Clips."

    if is_quiet:
        return

    elif not types:
        print(f"Found {len(extraction.highlights)} highlights.")
        print(f"Found {len(extraction.notes)} notes.")
        #print(f"Found {len(extraction.bookmarks)} bookmarks.")
        return

    else:
        if 'highlights' in types:
            print(f"Found {len(extraction.highlights)} highlights.")

        if 'notes' in types:
            print(f"Found {len(extraction.notes)} notes.")

        # if 'bookmarks' in types:
        #     print(f"Found {len(extraction.bookmarks)} bookmarks.")

        return

### ARGUMENT PARSING AND MAIN LOGIC
######################################################################

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

types_of_clip = parser.add_argument_group()

types_of_clip.add_argument('-H', '--highlights', dest='types',
                           action='append_const', const='highlights',
                           help='''If used, the clips extracted will
                           contain highlights. The default is all type
                           of clips.''')

types_of_clip.add_argument('-n', '--notes', dest='types',
                           action='append_const', const='notes',
                           help='''If used, the clips extracted will
                           contain notes. The default is all type of
                           clips.''')

types_of_clip.add_argument('-b', '--bookmarks', dest='types',
                           action='append_const', const='bookmarks',
                           help='''If used, the clips extracted will
                           contain bookmarks. The default is all type
                           of clips.''')

parser.add_argument('-q', '--quiet', action='store_true',
                    help="Dont't print any message.")

args = parser.parse_args()

if __name__ == '__main__':

    # Initial message
    if not args.quiet: print(f"Processing '{args.file}'.")

    # Get extracted clips
    extraction: Extraction = parse_rawclips_file(args.file)
    results: list[Clip] = []

    # Print messages about extracted and requested clips
    print_extraction_messages(args.quiet, extraction, args.types)

    # Define which type of the extracted clips are needed by request
    # of the user; the others are not used
    if not args.types:
        results = extraction.highlights + extraction.notes

    else:
        if 'highlights' in args.types:
            results.extend(extraction.highlights)

        if 'notes' in args.types:
            results.extend(extraction.notes)

        # if 'bookmarks' in args.types:
        #     results.extend(extraction.bookmarks)

    # Print to stdout or write to requested file
    if args.output_file is None:
        print(format_clips(results, args.format))
    else:
        with open(args.output_file, mode='w', encoding='utf-8') as file:
            file.write(format_clips(results, args.format))

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

def test_parse_time_info():
    assert parse_time_info('11:59:59 PM') == time(23, 59, 59)
    assert parse_time_info('12:00:00 AM') == time(0, 0, 0)
    assert parse_time_info('12:00:01 AM') == time(0, 0, 1)
    assert parse_time_info('11:59:59 AM') == time(11, 59, 59)
    assert parse_time_info('12:00:00 PM') == time(12, 0, 0)
    assert parse_time_info('12:00:01 PM') == time(12, 0, 1)

def test_pages_and_loc_to_str():
    assert pages_and_loc_to_str([]) == 'no data'
    assert pages_and_loc_to_str([1]) == '1'
    assert pages_and_loc_to_str([1, 5]) == '1-5'
    assert pages_and_loc_to_str([1, 5, 10]) == '1, 5, 10'
