import csv
import statistics

durations = []

with open('fast_a_better_vB_100.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    with open('../api-tests/resources/bpmn/fast_a_better/fast_a_better_vB_100.json', 'w+') as txt_file:
        txt_file.write("{\n")
        txt_file.write('"durations": [\n')
        for row in csv_reader:
            durations.append(float(row[3]))
            txt_file.write(str(row[3]) + ',\n')
        txt_file.write('],\n')
        txt_file.write('"interarrivalTime": ' + str(statistics.fmean(durations)) + '\n')
        txt_file.write('}')
