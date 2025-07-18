from __future__ import annotations

import argparse
import pandas as pd
import re
import reprlib

import pymupdf

from dataclasses import dataclass, field

class HeaderError(Exception):
    pass

@dataclass
class Padron:
    studentRegisters: list[StudentRegister]
    def padron(self) -> list[StudentRegister]:
        return self.studentRegisters
    def register(self, i:int) -> StudentRegister:
        return self.studentRegisters[i]
    def add_register(self, register:StudentRegister) -> None:
        self.studentRegisters.append(register)
    def get_numRegisters(self) -> int:
        return len(self.studentRegisters)
    def get_metadata(self, i:int) -> dict[str, str]:
        register = self.padron()[i]
        return register.get_metadata()
    def get_registersFromMetadata(
        self, metadata: dict[str, str | int]
    ) -> list[StudentRegister]:
        """
        Returns the studentRegisters that contain the given 'metadata'. The
        values used in the 'metadata' dictionary can be substrings of the
        correponding values in this instance metadata, e.g, the entry
        "CARRERA":"INFORMATICA" will match "CARRERA":"1 LICENCIATURA EN
        INFORMATICA".

        Note: The studentRegister instances are however not copied (just
        new pointers); if modified, the changes will also be reflected in the
        original Padron's studentRegisters attribute.
        """
        registers = self.padron()
        keys = metadata.keys()
        studentRegisters = []
        # For each StudentRegister instance in the Padron
        for register in registers:
            # Check if all key, value pairs in metadata are found
            found = True
            register_meta = register.get_metadata()
            for key in keys:
                sought = str(metadata[key])
                if(sought not in register_meta[key]):
                    found = False
                    break
            if(found): studentRegisters.append(register)
        return studentRegisters
    def info(self) -> None:
        N = self.get_numRegisters()
        if(N==0): print("Empty Padron")
        for i in range(N):
            print(f"Page {i}:")
            print("\n".join(f"{label}: {val}" for label, val in
                            self.get_metadata(i).items()) + "\n")
    def __repr__(self) -> str:
        repr = '{}({})'
        cls = self.__class__.__name__
        # reprlib will shorten long strings and maximum number of list elements
        my_repr = reprlib.Repr()
        my_repr.maxlist = 3
        my_repr.maxother = 62
        return repr.format(cls, my_repr.repr(self.studentRegisters))

@dataclass
class PadronCarrera(Padron):
    major:str
    school:str
    plan:int
    def get_students(self) -> pd.DataFrame:
        tags = ['PERIODO', 'GRUPO']
        df = pd.DataFrame({})
        row_labels = []
        for register in self.padron():
            dataframe =  register.get_students()
            metadata = register.get_metadata()
            for tag in tags:
                value = metadata[tag]
                dataframe[tag] = value
            df = pd.concat([df, dataframe], axis=0, ignore_index=True)
        return df
    def __repr__(self) -> str:
        string = super().__repr__()
        new = f", major={self.major}, school={self.school}, plan={self.plan})"
        return string[:-1] + new

@dataclass
class Page:
    """Class to store information of a page extracted from a pdf"""
    lines: list[str]
    headerSize: int = 0
    footerSize: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def numLines(self) -> int:
        return len(self.lines)
    def get_headerSize(self) -> int:
        return self.headerSize
    def get_footerSize(self) -> int:
        return self.footerSize
    def get_bodySize(self) -> int:
        N = self.numLines() - (self.get_footerSize() + self.get_headerSize())
        return N
    def get_metadata(self):
        return self.metadata
    def get_header(self) -> str:
        N = self.get_headerSize()
        return "\n".join(self.lines[:N])
    def get_footer(self) -> str:
        N = self.get_footerSize()
        return "\n".join(self.lines[-N:])
    def read(self) -> str:
        return "\n".join(self.lines)
    def readlines(self) -> list[str]:
        return self.lines
    def readbody(self) -> list[str]:
        N = self.get_bodySize()
        idx = self.get_headerSize()
        return self.lines[idx:idx+N]
    def set_metadata(self, metadata:dict[str, str]):
        self.metadata = metadata
    def remove_empty_lines(self) -> None:
        """Lines with no characters or just white spaces are removed"""
        non_empty_lines = [line for line in self.lines if line.strip()]
        self.lines = non_empty_lines
    def remove_white_space(self) -> None:
        """Removes spaces at start and end of each line"""
        no_spaces = [line.strip() for line in self.lines]
        self.lines = no_spaces
    def allCapsNoAccents(self) -> None:
        """
        Modifies page: puts all text in caps and removes accents
        """
        for i, line in enumerate(self.lines):
            self.lines[i] = line.upper().translate(del_accents())
        return None
    def analizeHeader(self, sep:str = ':'):
        """
        Sets the metadata attribute using the header fields defined by the
        separator 'sep'.

        Fields:
            If there are more than one separators in a line, the words
            immediately before them are stored as keys and the words that are
            in between the keys are the values. When there's just one 'sep' the
            word before it is the key and the rest of the line is the value.
        """
        data = {}
        N = self.get_headerSize()
        for j in range(N):
            line = self.lines[j]
            # If the separator is found extract info
            if(sep in line):
                vals = []
                keys = []
                fields = [field.strip() for field in line.split(sep)]
                for field in fields[:-1]:
                    key_idx = field.rfind(' ') + 1
                    vals.append(field[:key_idx].rstrip())
                    keys.append(field[key_idx:])
                vals.append(fields[-1])
                data.update({keys[i]:vals[i+1] for i in range(len(keys))})
        self.metadata = data
    def __str__(self) -> str:
        return "\n".join(self.lines)
    def __repr__(self) -> str:
        cls = self.__class__.__name__
        string = '{}({}, headerSize={!r}, footerSize={!r}, metadata={!r})'
        # reprlib will shorten long strings and maximum number of list elements
        return string.format(cls, reprlib.repr(self.lines),
                             self.get_headerSize(),
                             self.get_footerSize(),
                             self.get_metadata())

@dataclass
class StudentRegister(Page):
    headerSize: int | None = None
    footerSize: int | None = None

    def is_id(self, string:str) -> bool:
        # The ID must have the following form:
        # starts with one or more digits then a dash (-) and then one digit
        pattern = r"^\d+-\d$"
        return bool(re.search(pattern, string))
    def can_be_name(self, string) -> bool:
        """
        Assumes that string has been stripped (no spaces at start or end),
        has capital letters only and no accents.

        The string can be a name (returns True) if it only contains characters
        in the spanish alphabet and has more than two words (two last names and
        at least one first name). There's a list of words in the method which
        exclude the possibility that the 'string' be considered a name.
        """
        # Matches alphabetic characters in Spanish and spaces
        pattern = r"^[A-ZÑÜ ]+$"
        # 'string' is not a good name if it contains any of these words
        exclude = ["NOMBRE", "ALUMNO"]
        if(re.search(pattern, string)):
            if(len(string.split())>2):
                if not any(elem in string for elem in exclude):
                    return True
        return False
    def findSections(self) -> None:
        """
        Tries to find the sections on the student register: header, body, and
        footer; it sets the headerSize and footerSize attributes.

        A StudentRegister must always have a nonempty header. As such, this
        method returns an Exception if header is not found.

        Assumes the text has been processed to have capital letters only and no
        accents. (See self.allCapsNoAccents)

        Header:
            The header is defined as the section from the top of the page and
            before the first line where a student name or ID show up. Else,
            before the footer is reached.
        Footer:
            The lines at the bottom that contain 'TOTAL DE ALUMNOS POR GRUPO'
            and the respective integer. No other words can be in between and
            these must be the last lines of the page.
        """
        def first_student(lines) -> int | None:
            """Returns index of first student or None if no student is found"""
            N = len(lines)
            for i, line in enumerate(lines):
                if(self.is_id(line)):
                    if(i==0):
                        if(self.can_be_name(lines[i+1])):
                            return 0
                    elif(i==N-1):
                        if(self.can_be_name(lines[i-1])):
                            return i-1
                    elif(self.can_be_name(lines[i-1])):
                        return i-1
                    elif(self.can_be_name(lines[i+1])):
                        return i
                    raise Exception(f"Found student ID but not his name (ID: {line})")
            return
        def has_footer(lines, linesFooter):
            assert(linesFooter==2)
            footer_keyword = 'TOTAL DE ALUMNOS POR GRUPO'
            for i, line in enumerate(lines[-linesFooter:]):
                if(line.isdecimal()):
                    # Check the other line for the footer_keyword
                    string = lines[-1-i].translate(del_punctuation()).strip()
                    if(string==footer_keyword):
                        # Footer has been found
                        return True
            return False

        lines = self.readlines()
        # Look for first student and update headerSize
        headerSize = first_student(lines)
        # It is not allowed to have an empty header
        if(headerSize == 0): raise HeaderError("empty header")

        # Find footer and update footerSize
        footerSize = 0
        linesFooter = 2
        if(has_footer(lines, linesFooter)):
            footerSize = linesFooter

        # If no students were found, check if there's a footer and update
        # headerSize
        if(not headerSize):
            if(footerSize):
                headerSize = self.numLines() - footerSize
            else:
                raise HeaderError("invalid header: no student, no footer")
        self.headerSize = headerSize
        self.footerSize = footerSize

    def analizeHeader(self, sep:str = ':'):
        def update_data(pattern, header, kwd, data):
            match = re.search(pattern, header)
            if(match):
                data[kwd] = match.group(1).strip()
        school_kwd = 'ESCUELA'
        major_kwd = 'CARRERA'
        other_kwd = ['PLAN', 'PERIODO', 'GRUPO']

        kwd_pattern = lambda kwd: kwd + r"\s*" + sep + r"\s*"
        pattern_school = kwd_pattern(school_kwd) + r"(\d+[A-Z ]+)\n"
        major_split = other_kwd[0]
        pattern_major = kwd_pattern(major_kwd) + r"(\d[A-Z ]+)" + major_split
        pattern_other = [kwd_pattern(kwd) + r"(\d)" for kwd in other_kwd]

        all_patterns = [pattern_school, pattern_major, *pattern_other]
        all_kwd = [school_kwd, major_kwd, *other_kwd]

        header = self.get_header()
        data = {kwd:None for kwd in all_kwd}
        for i, pattern in enumerate(all_patterns):
            update_data(pattern, header, all_kwd[i], data)

        # Try to find major if major_kwd was not found
        if(data[major_kwd] is None):
            pattern = (sep + r"\s*" + r"(\d\s*LICENCIATURA[A-Z, ]+)" +
                       major_split)
            update_data(pattern, header, major_kwd, data)
        self.metadata.update(data)

    def get_students(self) -> pd.DataFrame:
        def check_names(name):
            if(len(name.split()) < 3):
                print(f"Student name with fewer than three words: {name}")
            if(re.search(r"\d", name)):
                print(f"Student name with a digit: {name}")
        def check_ids(id):
            if(not self.is_id(id)):
                print(f"Wrong ID: {id}")
        def check_student(tag, student):
            if(tag=='id'):
                return check_ids(student)
            elif(tag=='name'):
                return check_names(student)
            else:
                raise Exception("bad tag: use 'id' or 'name'")
        cols = ['id', 'name']
        data = {col:[] for col in cols}
        student_info = self.readbody()
        # Students are given by name and id in separate lines of 'self.lines'.
        # Sometimes the 'name' comes before the 'id' or the other way around.
        # (Depending on what pdf reader library was used.) The following takes
        # care of that
        if(student_info):
            # A name entry must have more than one word
            numWords = len(student_info[0].split())
            if(numWords > 1): cols.reverse() # name comes before id
        for i, student in enumerate(student_info):
            col = cols[i%2]
            check_student(col, student)
            data.get(col).append(student)
        return pd.DataFrame(data= data)

    def __repr__(self) -> str:
        return super().__repr__()


def read_pdf(filename: str) -> list[list[str]]:
    """
    Turns pdf file into strings. It returns a list of pages, each page
    defined by a list of its lines.

    Rules: No empty lines are returned. No whitespaces at start or end of line.
    """
    doc = pymupdf.open(filename)
    pages = []
    for page in doc:
        # The get_text function automatically removes  empty lines
        # and white spaces at start or end of line
        pages.append(page.get_text().splitlines())
    return pages

def del_accents():
    return str.maketrans({'Á': 'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U'})

def del_punctuation():
    return str.maketrans({':' : '', ',' : '', '.' : ''})

def create_tables(filename: str):
    doc = read_pdf(filename)
    pages = []
    for i, page_lines in enumerate(doc):
        page = StudentRegister(page_lines)
        page.allCapsNoAccents()
        page.findSections()
        page.analizeHeader()
        pages.append(page)
    return Padron(pages)


if(__name__ == '__main__'):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filename', type=str
    )
    args = parser.parse_args()
    create_tables(args.filename)
