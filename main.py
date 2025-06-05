import glob

import numpy as np
import pandas as pd

# def investigate_these(df, semester, student_id):
#     "Returns list of students from desired semester whom to investigate"
#     col = semester - 1  # transform to python index
#     student = df.iloc[student_id, col]
#     print(student)
#     res = np.where(df == student)
#     print(res)
#     # I'm only interested in checking students from that show up
#     # from the current semester on
#     if( min(res[1]) == col):
#         print("Requires checking")
#     else:
#         print("Does not require checking")

class Hist(object):
    def __init__(self) -> None:
        self.records = []
    def add_generation(self, year, record):
        self.records.append((year, record))
    def __str__(self) -> str:
        msg = ""
        for year, record in self.records:
            msg += str(year) + ":" + str(record) + str("\n")
        return msg
    def __repr__(self) -> str:
        return self.__str__()

class Student(object):
    def __init__(self, name, hist) -> None:
        "The student code can be zero or one"
        self.name = name
        self.hist = hist

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

def investigate_these(df, year, semester):
    "Returns list of students from desired semester whom to investigate"
    col = semester - 1  # transform to python index
    students = df.iloc[:, col]
    pupils = []
    # Loop through each student (avoid NaN)
    for student in students[students.notna()]:
        # print(index, student)
        # Student history
        id, sem = np.where(df == student)
        # print(res)
        # I'm only interested in checking students from that show up
        # from the current semester on
        if( min(sem) == col):
            history = Hist()
            # Add  history sorted by semester
            record = order_record((id, sem))
            # idx = np.argsort(sem)
            # history.add_generation(year, (id[idx], sem[idx]))
            history.add_generation(year, record)
            pupils.append(Student(student, history))
            print(student)
            print(record)
            # Notify if a student finished his/her bachelor's
            if(record[1][-1] == 9):
                print("Finished bachelor's")
            print()
    return pupils

def search_across_gens(name, init_gen, database):
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
                print(year)
                print(record)
                histories.add_generation(year, record)
    return histories

# Load student generations dataframe
gen  = load_database()
