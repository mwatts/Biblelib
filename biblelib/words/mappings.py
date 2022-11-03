"""Read and write word-level mappings.

Source data is in ../sources/Clear/mappings/mappings-GNT-stripped.tsv.

Examples:
    >>> import mappings


"""

from collections import UserList
from csv import DictReader, DictWriter
from dataclasses import asdict, dataclass, field
from pathlib import Path

# This directory: mappings-GNT-stripped.tsv is located relative to
# this in a sibling repository
WORDSPATH = Path(__file__).parent
# Content from https://github.com/Clear-Bible/
CLEARPATH = WORDSPATH.parent.parent.parent


@dataclass
class ClearID:
    """Identifies words from Bible texts by book, chapter, verse, ord, and word part.

    This supports two formats: BBCCCVVVWWW and BBCCCVVVWWWP, where BB
        identifies a book, CCC identifies a chapter number, VVV
        identifies a verse number, and WWW identifies a word number
        within that verse. If P is present it identifies a word part:
        this is only used for Hebrew.

    This dataclass does not validate whether any identifiers are in
    the correct range: it only records the data. Use TBD for
    validation.

    Attributes:
        book_ID: 2-character string identifying the Bible book using
            USFM numbers (like '40' for Matthew)
        chapter_ID: 3-character string identifying a chapter number
            within the book
        verse_ID: 3-character string identifying the verse number
        word_ID: 3-character string identifying the word number
        part_ID: single character identifying the word part if
            present: only used for Hebrew

    See `books.Books.fromusfmnumber()` for how to convert this number
    to other Book identifiers.

    """

    ID: str
    book_ID: str = field(init=False)
    chapter_ID: str = field(init=False)
    verse_ID: str = field(init=False)
    word_ID: str = field(init=False)
    part_ID: str = field(init=False, default="")

    def __post_init__(self) -> None:
        """Compute other values on initialization."""
        assert 12 >= len(self.ID) >= 11, "Invalid length: {self.ID}"
        self.book_ID = self.ID[:2]
        self.chapter_ID = self.ID[2:5]
        self.verse_ID = self.ID[5:8]
        self.word_ID = self.ID[8:11]
        if len(self.ID) == 12:
            self.part_ID = self.ID[11]
            # TODO: add tests, presumably a closed set of values

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<ClearID: {self.ID}>"


@dataclass
class Mapping:
    """Dataclass mapping words across various Greek NTs.

    These are typically read from a TSV file and instantiated by other
    code. Words are identified with the Clear format of an 11-digit
    BBCCCVVVWWW identifier: see documentation for details. Text values
    are UTF-8 encoded, with final punctuation attached.

    Attributes:
        NA1904_ID: the identifier for this word in Nestle-Aland 1904
        NA1904_Text: the word form in Nestle-Aland 1904
        NA27_ID: the identifier in Nestle-Aland 27th Edition
        NA28_ID: the identifier in Nestle-Aland 28th Edition
        SBLGNT_ID: the identifier in SBL GNT
        SBLGNT_Text: the word form in SBL GNT
        MARBLE_ID: the identifier in Project MARBLE

    """

    # Named to match column headers in source TSV
    # Greek New Testament, edited by Eberhard Nestle
    NA1904_ID: str
    # text element
    NA1904_Text: str
    # Nestle-Aland 27th Edition
    NA27_ID: str
    # Nestle-Aland 28th Edition
    NA28_ID: str
    # https://sblgnt.com/
    SBLGNT_ID: str
    # text element
    SBLGNT_Text: str
    # USB MARBLE project: https://semanticdictionary.org/
    MARBLE_ID: str

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<Mapping: {self.NA1904_ID}>"


class Mappings(UserList):
    """Manage a sequence of Mapping instances."""

    # relative path assuming you have a local copy of the macule-greek repo
    source: Path = CLEARPATH / "macula-greek/sources/Clear/mappings/mappings-GNT-stripped.tsv"
    mappingfields: list = list(Mapping.__dataclass_fields__.keys())

    def __init__(self, sourcefile: str = "") -> None:
        """Initialize Mappings."""
        super().__init__()
        if sourcefile:
            self.source = Path(sourcefile)
        assert self.source.exists(), f"No file {self.source}: do you have a local copy of the macula-greek repository?"
        with self.source.open(encoding="utf-8") as f:
            reader: DictReader = DictReader(f, dialect="excel-tab")
            # make sure the fieldnames in the file are the same as the
            # dataclass attributes
            fieldnameset: set = set(reader.fieldnames[0].split("\t"))
            assert not fieldnameset.difference(
                self.mappingfields
            ), f"Fieldname discrepancy header: {fieldnameset} vs {self.mappingfields}"
            self.data: list = [Mapping(**r) for r in reader]

    # short-term need
    def _add_prefix(
        self, outfile: str = CLEARPATH / "macula-greek/sources/Clear/mappings/mappings-GNT-corrected.tsv"
    ) -> None:
        """Rewrite the source, adding 'n' to NA1904_ID values."""
        outpath = Path(outfile)
        with outpath.open("w", encoding="utf-8") as f:
            writer: DictWriter = DictWriter(f, fieldnames=self.mappingfields, dialect="excel-tab")
            writer.writeheader()
            for mapping in self.data:
                mapping.NA1904_ID = "n" + mapping.NA1904_ID
                writer.writerow(asdict(mapping))
