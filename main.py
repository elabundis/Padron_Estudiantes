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
    def get_label(self, year):
        return self.labels[str(year)]
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

class Classification(object):
    def __init__(self, generations) -> None:
        self.generations = generations
    def get_years(self):
        return list(self.generations.keys())
    def get_generation(self, year):
        """
        Returns list of students corresponding to 'year'
        """
        return self.generations[str(year)]
    def get_first_generation(self):
        first_year = np.min( np.array(self.get_years(), dtype=int) )
        return self.get_generation(first_year)
    def get_student_instance(self, name):
        """
        We assume all students share the same first generation
        """
        first_gen_students = self.get_first_generation()
        for student in first_gen_students:
            if(student.name == name):
                return student
        print(f"No student found with name {name}. Returning None")
        return None
    def get_student_label(self, student, year):
        return student.hist.get_label(year)
    def print_student_labels(self, student):
        years = student.hist.get_generations()
        msg = ""
        for year in years:
            msg += f"year {year}:" + self.get_student_label(student, year) + "\n"
        print(msg)
    def order_data(self):
        years =  np.sort(np.array(list(self.generations.keys()), dtype=int))
        self.idx = {str(years[i]):i for i in range(len(years))}
        self.names = [[] for i in range(len(years))]
        self.locs = [[] for i in range(len(years))]
        self.labels = [[] for i in range(len(years))]
        for i, year in enumerate(years):
            students = self.get_generation(year)
            for student in students:
                self.labels[i].append(self.get_student_label(student, year))
                self.locs[i].append(student.hist.get_record(year))
                self.names[i].append(student.name)
    def get_all_labels(self, year):
        idx = self.idx[str(year)]
        return list(set(self.labels[idx]))
    def get_labels_and_locs(self, year):
        idx = self.idx[str(year)]
        return [(loc, label) for loc, label in zip(self.locs[idx], self.labels[idx])]
    def get_locations(self, year, label):
        """
        Indices start at 1 to reduce confusion
        """
        idx = self.idx[str(year)]
        locations = []
        for i, label_database in enumerate(self.labels[idx]):
            if(label == label_database):
                loc = ((int(self.locs[idx][i][0][0]) + 1, int(self.locs[idx][i][1][0]) +
                       1),  self.names[idx][i])
                locations.append(loc)
        return locations
    def print_all_locations(self, year):
        """
        Indices start at 1 to reduce confusion
        """
        # All labels for given generation
        labels = self.get_all_labels(year)
        for label in labels:
            print(label)
            for loc in self.get_locations(year, label):
                print(loc)
            print()

    def get_particular_classification(self, year, label):
        tags = self.get_labels_and_locs(year)
        desired_tags = []
        for tag in tags:
            if(tag[1] == label):
                desired_tags.append(tag)
        return desired_tags


def load_database():
    directory = "Databases/"
    prefix = "generacion_"
    year_init  = 2015
    year_final = 2023
    generation = {}

    numFiles = year_final - year_init + 1
    year = year_init
    print("Files: ")
    for i in range(numFiles):
        filename = glob.glob(directory + prefix + str(year) + "*")[0]
        print(filename)
        generation[str(year)] =  pd.read_csv(filename)
        year += 1
    return generation

def order_record(record):
    id, semester = record
    idx = np.argsort(semester)
    return (id[idx], semester[idx])

def student_finished_generation(semesters, generation):
    if(generation < 2020):
        max_semester = 9
    else:
        max_semester = 9 - 2*(generation-2019)
    return max_semester in semesters

def did_student_finish(student_hist):
    last_gen = student_hist.get_last_generation()
    if(last_gen < 2020):
        max_semester = 9
    else:
        max_semester = 9 - 2*(last_gen-2019)
    return student_hist.has_semester(last_gen, max_semester)

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
        # who did not study until the final semester (might have missed a
        # semester in between)
        if(semester == 1):
            if(not student_finished_generation(sem, year)):
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
    init_sem = min(classified[str(init_gen)][0].hist.get_semesters(init_gen))
    for gen in generations:
        students = classified[str(gen)]
        for student in students:
            history = student.hist
            if(gen == init_gen and init_sem == 0):
                if(len(history.get_generations())==1):
                    history.add_label(gen, 'desercion de la cohorte')
                else:
                    history.add_label(gen, 'rezago de la cohorte')
            elif(gen == init_gen):
                if(len(history.get_generations())==1):
                    # I count as finished if they reach the tenth semester
                    if(history.has_semester(gen, 9)):
                        history.add_label(gen, 'revalidaciones recibidas')
                    # When they reach the last semester of a given generation
                    # but that semester is not the 10th I consider they're
                    # still studyng
                    elif(did_student_finish(history)):
                        # Still studying
                        history.add_label(gen, 'revalidaciones recibidas')
                    else:
                        history.add_label(gen, 'desercion de revalidaciones')
                else:
                    # It is possible that a student participates in a future
                    # generation even if he finishes in the current one (he
                    # takes a class from the generation preceding him while
                    # still taking his classes)
                    sems = history.get_semesters(gen) # semesters he participates
                                                      # in current generation
                    if(student_finished_generation(sems, gen)):
                        history.add_label(gen, 'revalidaciones recibidas')
                        msg = f"student {student.name} finished in year {gen} "
                        msg += "but also participates in future years"
                        print(msg)
                    else:
                        history.add_label(gen, 'rezago de revalidaciones')
            else:
                # student has appeared in a previous generation
                student_gens = np.array(history.get_generations(),
                                               dtype=int)
                participates_in_later_gens = np.any(student_gens>gen)
                participates_in_initGen_SemOne = history.has_semester(init_gen, 0)
                if(participates_in_later_gens):
                    if(participates_in_initGen_SemOne):
                        history.add_label(gen, 'rezago de la cohorte')
                    else:
                        history.add_label(gen, 'rezago de revalidaciones')
                else:
                    # this is their last participation
                    # Check if student finished in his last participation
                    finished = did_student_finish(history)
                    if(finished):
                        if(gen < 2020):
                            if(participates_in_initGen_SemOne):
                                history.add_label(gen, 'rezago recibido')
                            else:
                                history.add_label(gen, 'revalidaciones recibidas')
                        # Might provide special labels in the future for those
                        # who are not done yet
                        else:
                            # Still studying
                            if(participates_in_initGen_SemOne):
                                history.add_label(gen, 'rezago recibido')
                            else:
                                history.add_label(gen, 'revalidaciones recibidas')
                    else:
                        if(participates_in_initGen_SemOne):
                            history.add_label(gen, 'desercion de rezago recibido')
                        # He might have finished in his initial generation and
                        # have just taken some course in this one. For such a
                        # case I do not have a label at the moment
                        elif(student_finished_generation(
                                    history.get_semesters(init_gen), init_gen)):
                            history.add_label(gen, 'unknown')
                            msg = f"Label is 'unknown' for {student.name} "
                            msg += f"during generation {gen} "
                            msg += "(fisnished in his first generation)"
                            print(msg)
                        else:
                            history.add_label(gen, 'desercion de revalidaciones')
    return classified

def classify_students(students):
    classified_gens = classify_and_label(students)
    classified = Classification(classified_gens)
    classified.order_data()
    return classified

def create_classification(semester, generation, database):
    students = investigate_all(semester, generation, database)
    classified = classify_students(students)
    return classified

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

def student_history(name, database):
    years = np.sort(np.array(list(database.keys()), dtype=int))
    found = False
    for year in years:
        df = database[str(year)]
        inCurrentGen = df.isin([name]).any().any()
        if(inCurrentGen):
            print(f"found in year {year}")
            id, sem = np.where(df == name)
            record = order_record((id, sem))
            print(record)
            found = True
    if(not found): print(f"{name} not found")
