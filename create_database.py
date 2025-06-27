import argparse
import re

def create_tables(filename):
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
