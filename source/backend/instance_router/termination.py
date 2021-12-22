import pycamunda.processinst

url = 'http://localhost/engine-rest'

get_instances = pycamunda.processinst.GetList(url, process_definition_key='MyProcess')
instances = get_instances()

for instance in instances:
    print('Process instance id:', instance.id_)