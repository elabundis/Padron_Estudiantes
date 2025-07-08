import argparse
import re
import reprlib

import pymupdf

from dataclasses import dataclass, field

@dataclass
class Page:
    """Class to store information of a page extracted from a pdf"""
    lines: list[str]
    headerSize: int = 0
    footerSize: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def get_size(self) -> int:
        return len(self.lines)
    def get_headerSize(self) -> int:
        return self.headerSize
    def get_footerSize(self) -> int:
        return self.footerSize
    def get_bodySize(self) -> int:
        N = self.get_size() - (self.get_footerSize() + self.get_headerSize())
        return N
    def get_metadata(self):
        return self.metadata
    def get_text(self) -> str:
        N = self.get_size()
        return "\n".join(self.lines[:N])
    def get_header(self) -> str:
        N = self.get_headerSize()
        return "\n".join(self.lines[:N])
    def get_footer(self) -> str:
        N = self.get_footerSize()
        return "\n".join(self.lines[-N:])
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
            self.lines[i] = line.upper().translate(translator())
        return None
    def analizeHeader(self, sep:str = ':'):
        """
        Retrieves information from the fields defined by the separator 'sep' in
        a dictionary and sets the metadata parameter.

        Header:
            The header is defined as the section from the top of the page until
            the line where student names and ID's show up.
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
    headerSize: int = 8
    footerSize: int = 2
    def get_students(self):
        def check_names(name):
            if(len(name.split()) < 3):
                print(f"Student name with fewer than three words: {name}")
            if(re.search(r"\d", name)):
                print(f"Student name with a digit: {name}")
        def check_ids(id):
            # The ID must have the following form:
            # starts with one or more digits then a dash (-) and then one digit
            pattern = r"^\d+-\d$"
            if(not re.search(pattern, id)):
                print(f"Wrong ID: {id}")
        def check_student(code, student):
            if(code==0):
                return check_ids(student)
            elif(code==1):
                return check_names(student)
            else:
                raise Exception("bad code: use '0' for ids and '1' for names")
        student_info = self.readbody()
        students = [[], []] # First col. IDS, second col. names
        # Students are given by name and id in separate lines of 'self.lines'.
        # Sometimes the 'name' comes before the 'id' or the other way around.
        # (Depending on what pdf reader library was used.) The following takes
        # care of that
        first_name = len(student_info[0]) > 1  # A name entry must have more
                                               # than one word
        if(first_name):
            codes = [1, 0]
        else:
            codes = [0, 1]
        for i, student in enumerate(student_info):
            code = codes[i%2]
            check_student(code, student)
            students[code].append(student)
        return students


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

def translator():
    return str.maketrans({'Á': 'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U'})

def tables(filename: str):
    doc = read_pdf(filename)
    pages = []
    for i, page_lines in enumerate(doc):
        page = StudentRegister(page_lines, headerSize=8, footerSize=2)
        page.allCapsNoAccents()
        page.analizeHeader()
        pages.append(page)
    return pages

def create_tables(filename):
    """
    Assumes txt file of a 'Padron' pdf has been created using py2pdf
    """
    with open(filename, 'r') as reader:
        semesters = []
        ids = []
        names = []
        # periodo = r"PERIODO: \d+"
        periodo = "PERIODO:"
        career = "licenciatura en informatica"

        translator = str.maketrans('á', 'a')
        line = reader.readline()
        while(line != ''):
            line_words = line.split()
            # for empty lines
            # if(line.strip()==''):
            #     print(f"line {i+1} is empty", end='')
            # periodo_found = re.search(periodo, line)
            periodo_found = periodo in line_words
            if(periodo_found):
                filtered_line =  line.lower().translate(translator)
                # Stop at the minute you find a different career
                if(career not in filtered_line):
                    return (semesters, ids, names)
                # sem = periodo_found.group().split(':')[1]
                idx = line_words.index(periodo) + 1
                sem = line_words[idx]
                print(f"retrieve semester: {sem}")
                semesters.append(sem)
                ids.append([])
                names.append([])
            if("ALUMNO" in line_words):
                reader.readline()
                is_id = True
                while(True):
                    line = reader.readline()
                    isEmpty = line.strip() == ''
                    if(isEmpty):
                        if(is_id):
                            is_id = False
                        else:
                            break
                    elif(is_id):
                        ids[-1].append(line.rstrip('\n'))
                    else:
                        names[-1].append(line.rstrip('\n'))
            line = reader.readline()
        return (semesters, ids, names)

if(__name__ == '__main__'):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filename', type=str
    )
    args = parser.parse_args()

    create_tables(args.filename)
