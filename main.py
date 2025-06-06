import glob

import numpy as np
import pandas as pd

class Hist(object):
    def __init__(self) -> None:
        self.records = {}
    def add_record(self, year, record):
        self.records[str(year)] = record
    def get_generations(self):
        return list(self.records.keys())
    def get_record(self, year):
        return self.records[str(year)]
    def get_data(self):
        return self.records
    def get_first_generation(self) -> int:
        return np.min( np.array(self.get_generations(), dtype=int) )
    def has_generation(self, year):
        return str(year) in self.records.keys()
    def delete_generation(self, year):
        del self.records[str(year)]
    def __str__(self) -> str:
        msg = ""
        for year, record in self.records.items():
            msg += year + ":" + str(record) + str("\n")
        return msg
    def __repr__(self) -> str:
        return self.__str__()

class Student(object):
    def __init__(self, name, hist) -> None:
        self.name = name
        self.hist = hist
    def add_history(self, history):
        new_records = history.get_data()
        self.hist.records.update(new_records)
    def __str__(self) -> str:
        msg = self.name + "\n"
        return msg + self.hist.__str__()
    def __repr__(self) -> str:
        return self.__str__()

def print_students(students):
    """
    Returns a generator function to call a student at a time (with function
    next)
    """
    for student in students:
        yield student

def order_record(record):
    id, semester = record
    idx = np.argsort(semester)
    return (id[idx], semester[idx])

def load_database():
    prefix = "generacion_"
    year_init  = 2015
    year_final = 2023
    generation = {}

    numFiles = year_final - year_init + 1
    year = year_init
    print("Files: ")
    for i in range(numFiles):
        filename = glob.glob(prefix + str(year) + "*")[0]
        print(filename)
        generation[str(year)] =  pd.read_csv(filename)
        year += 1
    return generation

def investigate(df, year, semester, verbose=False):
    "Returns list of students from desired semester whom to investigate"
    col = semester - 1  # transform to python index
    students = df.iloc[:, col]
    pupils = []
    # Loop through each student (avoid NaN)
    for student in students[students.notna()]:
        add_student = False
        # Student history
        id, sem = np.where(df == student)
        # For people starting at first semester I'm only interested in those
        # who did not study from the first to the tenth semester
        if(semester == 1):
            if(not np.array_equal(np.sort(sem), np.arange(10)) ):
                add_student = True
        # Else, I'm only interested in checking students that show up from the
        # current semester on
        elif( min(sem) == col):
            add_student = True
        if(add_student):
            history = Hist()
            # Add  history sorted by semester
            record = order_record((id, sem))
            # idx = np.argsort(sem)
            # history.add_record(year, (id[idx], sem[idx]))
            history.add_record(year, record)
            pupils.append(Student(student, history))
            if(verbose):
                print(student)
                print(record)
                # Notify if a student finished his/her bachelor's
                if(record[1][-1] == 9):
                    print("Finished bachelor's")
                print()
    return pupils

def remove_formerGen(students, generation, database):
    """
    Given a list 'students' of Student instances, remove those students that
    show up in generations former to the chosen 'generation'. Note: students
    at 'generation' and later are not touched. Assumes generations in database
    are consecutive.
    """
    years = np.sort(np.array(list(database.keys()), dtype=int))
    init_year = years[0]
    N = generation - init_year  # Num. of generations that precede 'generation'
    if(N == 0): return
    del_student = []
    modify_list = False
    for student in students:
        name = student.name
        year = init_year
        for i in range(N):
            df = database[str(year)]
            # Check if student shows up in this generation
            if(df.isin([name]).any().any()):
                del_student.append(student)
                modify_list = True
                print("Student to be deleted:", name)
                print(f"Shows up in generation: {year}")
                print()
                break # This student will be removed no need to check further
            year += 1
    if(modify_list):
        for student in del_student:
            students.remove(student)

def search_across_gens(name, init_gen, database, verbose=False):
    """
    Returns a Hist object with the records of student with given 'name'
    starting at desired generation 'init_gen' given the generations 'database'
    """
    histories =  Hist()
    for year, df in database.items():
        year = int(year)
        if(year >= init_gen):
            record = np.where(df == name)
            if(len(record[0]) != 0):
                record = order_record(record)
                if(verbose):
                    print(year)
                    print(record)
                histories.add_record(year, record)
    return histories

def investigate_all(semester, init_gen, database):
    """
    Returns list of students from desired semester whom to investigate across
    generations starting from 'init_gen'. Skips those students that show up in
    a generation former to 'init_gen' since they can be investigated using that
    generation.
    """
    # Students that require checking with history for initial generation
    students = investigate(database[str(init_gen)], init_gen, semester)
    # Remove those students who were present in former generations
    remove_formerGen(students, init_gen, database)
    # Add their histories in remaining generations
    for student in students:
        name = student.name
        histories = search_across_gens(name, init_gen+1, database)
        student.add_history(histories)
    return students


# Load student generations dataframe
if(__name__ == '__main__'):
    gen  = load_database()
