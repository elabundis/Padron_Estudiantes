import glob

import numpy as np
import pandas as pd

class Hist(object):
    def __init__(self) -> None:
        self.records = {}
        self.labels = {}
    def add_record(self, year, record):
        self.records[str(year)] = record
    def add_label(self, year, label):
        self.labels[str(year)] = label
    def get_generations(self):
        return list(self.records.keys())
    def get_record(self, year):
        return self.records[str(year)]
    def get_semesters(self, year):
        return self.get_record(year)[1]
    def get_data(self):
        return self.records
    def get_first_generation(self) -> int:
        return np.min( np.array(self.get_generations(), dtype=int) )
    def get_last_generation(self) -> int:
        return np.max( np.array(self.get_generations(), dtype=int) )
    def has_generation(self, year):
        return str(year) in self.records.keys()
    def has_semester(self, year, semester):
        """semester is an integer starting at zero"""
        return semester in self.get_record(year)[1]
    def delete_generation(self, year):
        del self.records[str(year)]
    def __str__(self) -> str:
        msg = ""
        for year, record in self.records.items():
            msg += year + ":" + str(record) + str("\n")
            msg += self.labels.get(year, "") + str("\n")
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
    n = 1
    for student in students:
        print(f"n = {n}")
        yield student
        n += 1

def did_student_finish(hist):
    last_gen = hist.get_last_generation()
    if(last_gen < 2020):
        max_semester = 9
    else:
        max_semester = 9 - 2*(last_gen-2019)
    return hist.has_semester(last_gen, max_semester)

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


def find_student(name, database):
    years = np.sort(np.array(list(database.keys()), dtype=int))
    found = False
    for year in years:
        inCurrentGen = database[str(year)].isin([name]).any().any()
        if(inCurrentGen):
            print(f"found in year {year}")
            found = True
    if(not found): print(f"{name} not found")

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
        # who did not study until the tenth semester (might have missed a
        # semester in between)
        if(semester == 1):
            if(max(sem) != 9):
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
    if(len(students)==0):  print("No students found to investigate")
    # Add their histories in remaining generations
    for student in students:
        name = student.name
        histories = search_across_gens(name, init_gen+1, database)
        student.add_history(histories)
    return students

def classify(students):
    """
    Returns dictinary with generations as keys that contain list of students
    that have spent at least one semester in such a generation
    """
    if(len(students)==0):
        print("The list of students is empty")
    generations = {}
    for student in students:
        for year in student.hist.get_generations():
            generations[year] = generations.get(year, []) + [student]
    return generations

def classify_and_label(students):
    classified = classify(students)
    if(classified == {}): return classified
    generations = np.sort(np.array( list(classified.keys()), dtype=int ))
    init_gen = generations[0]
    # Choose a student from the first generation and investigate initial
    # semester
    min_semester = min(classified[str(init_gen)][0].hist.get_semesters(init_gen))
    for gen in generations:
        students = classified[str(gen)]
        for student in students:
            history = student.hist
            if(gen == init_gen and min_semester == 0):
                if(len(history.get_generations())==1):
                    history.add_label(gen, 'desercion de la cohorte')
                else:
                    history.add_label(gen, 'rezago de la cohorte')
            elif(gen == init_gen):
                if(len(history.get_generations())==1):
                    if(history.has_semester(gen, 9)):
                        history.add_label(gen, 'revalidaciones recibidas')
                    else:
                        history.add_label(gen, 'desercion de revalidaciones')
                else:
                    history.add_label(gen, 'rezago de revalidaciones')
            else:
                # student has appeared in a previous generation
                student_gens = np.array(history.get_generations(),
                                               dtype=int)
                participates_in_later_gens = np.any(student_gens>gen)
                participates_in_initGen_initSem = history.has_semester(init_gen, 0)
                if(participates_in_later_gens):
                    if(participates_in_initGen_initSem):
                        history.add_label(gen, 'rezago de la cohorte')
                    else:
                        history.add_label(gen, 'rezago de revalidaciones')
                else:
                    # this is their last participation
                    finished = did_student_finish(history)
                    if(finished):
                        if(gen < 2020):
                            if(participates_in_initGen_initSem):
                                history.add_label(gen, 'rezago recibido')
                            else:
                                history.add_label(gen, 'revalidaciones recibidas')
                        # Do not provide final label if they finished after 2019
                        else:
                            history.add_label(gen, 'still studying')
                    else:
                        if(participates_in_initGen_initSem):
                            history.add_label(gen, 'desercion de rezago recibido')
                        else:
                            history.add_label(gen, 'desercion de revalidaciones')
    return classified


# Load student generations dataframe
if(__name__ == '__main__'):
    gen  = load_database()
