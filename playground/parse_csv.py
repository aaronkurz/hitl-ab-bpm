import csv

with open('2000a.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    txt_file = open('../api-tests/resources/bpmn/helicopter_license_fast/2000a.json', 'w+')
    txt_file.write("{\n")
    txt_file.write('"durations": [\n')
    for row in csv_reader:
        txt_file.write(str(row[3]) + ',\n')
    txt_file.write(']\n')
    txt_file.write('}')
    txt_file.close()
