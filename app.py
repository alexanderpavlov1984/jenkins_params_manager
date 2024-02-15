'''
Этот скрипт позволяет автоматизировать конфигурирование параметров задач Jenkins.
Параметры вносятся в файл jobs_parameters.yaml в формате:

---
# Params for the Jenkins jobs
name_a: PARAMETER_ONE
choices_a:
  - One
  - Two
  - Three
name_b: PARAMETER_TWO
choices_b:
  - One
  - Two
  - Three
...

Важно! Для ключей в jobs_parameters.yaml допустимы только названия:

name_буква_английского_алфавита 
choices_буква_английского_алфавита

При добавлении нового параметра, эту букву нужно изменять на следующую
букву английского алфавита.

Скрипт переводит yaml в xml-структуру в формате Jenkins-API, добавляет служебные xml-элементы необходимые для Jenkins-API,
получает список задач с сервера Jenkins и устанавливает их параметры в соответствии с
параметрами из .yaml файла(в) в директории со скриптом.
Скрипт проверят наличие параметра указанного в файле jobs_parameters.yaml для всех задач (freestyle projects, pipelines) 
на сервере Jenkins, если у задачи на сервере Jenkins есть параметр указанный в файле jobs_parameters.yaml, тогда для этой
задачи значения изменяются на значения из файла. Значения параметров не указанные в файле jobs_parameters.yaml не изменяются.
В версии 0.1.0 поддерживается только Choice Parameter !

Установка зависимостей:

pip3 install -r requirements.txt

Запуск скрипта:

python3 app.py jenkins_username jenkins_password


'''

__author__ = "Павлов Александр Станиславович"
__version__ = "0.1.0"
__maintainer__ = "Павлов Александр Станиславович"
__email__ = "pavlovas@tricolor.ru"
__status__ = "Development"

import jenkins
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
import yaml
from yaml.loader import SafeLoader
from sys import argv

script, first, second = argv

server = jenkins.Jenkins('http://51.250.87.0:8080/', username=first, password=second)
YAML_CONF_FILE = 'jobs_parameters.yaml'

def generate_choise_params_xml_from_yaml_file(parametr_name):
    '''Takes in a parametr name for the Jenkins job (pipeline), 
    returns the xml string for this parametr based on YAML_CONF_FILE.'''

    with open(YAML_CONF_FILE, 'r') as stream:
        try:
            # Converts yaml document to python object
            parameters_dic = yaml.load(stream, Loader=SafeLoader)
        except yaml.YAMLError as e:
            print(e)

    new_choice_parameter_definition = ''
    name_last_letter = ''
    choises = 'choices_'
    for key in parameters_dic.keys():
        if key[0:4] == 'name' and parameters_dic[key] == parametr_name:
            name_last_letter = key[len(key)-1:]
            choises += name_last_letter
            if '</hudson.model.ChoiceParameterDefinition>' in new_choice_parameter_definition:
                new_choice_parameter_definition += '\n'
            new_choice_parameter_definition += '<hudson.model.ChoiceParameterDefinition>\n'
            new_choice_parameter_definition += f'  <name>{parameters_dic[key]}</name>\n'
            new_choice_parameter_definition += '  <choices class="java.util.Arrays$ArrayList">\n'
            new_choice_parameter_definition += '    <a class="string-array">\n'
        elif key == choises:
            for param in parameters_dic[key]:
                new_choice_parameter_definition += f'    <string>{param}</string>\n'
            new_choice_parameter_definition += '    </a>\n'
            new_choice_parameter_definition += '  </choices>\n'
            new_choice_parameter_definition += '</hudson.model.ChoiceParameterDefinition>'

    return new_choice_parameter_definition

def generate_jenkins_freestyle_conf_from_yaml_file(job_name_str):
    '''Takes in a Jenkins job (pipeline) name, returns full xml string config for this job (pipeline).'''

    with open(YAML_CONF_FILE, 'r') as stream:
        try:
            # Converts yaml document to python object
            parameters_dic = yaml.load(stream, Loader=SafeLoader)
        except yaml.YAMLError as e:
            print(e)

    job_conf_xml = server.get_job_config(job_name_str)

    try:
        # generate a new job config.xml from the job params.yaml   
        root = ET.fromstring(job_conf_xml)

        parameter_definitions = root.find('properties').find('hudson.model.ParametersDefinitionProperty').find('parameterDefinitions')

        for key in parameters_dic.keys():
            if key[0:4] == 'name':
                for element in root.iter('hudson.model.ChoiceParameterDefinition'):
                    if element[0].text == parameters_dic[key]:
                        parameter_definitions.remove(element)
                        choice_xml = generate_choise_params_xml_from_yaml_file(parameters_dic[key])
                        choice_et = ET.fromstring(choice_xml)
                        parameter_definitions.append(choice_et)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        xml_modified = ElementTree.tostring(root, encoding='unicode')
    except:
        return job_conf_xml

    return xml_modified

def reconfigure_jenkins_jobs_params():
    jobs_list = server.get_jobs()
    for job in jobs_list:
        new_job_conf = generate_jenkins_freestyle_conf_from_yaml_file(job['name'])
        server.reconfig_job(job['name'], new_job_conf)
 
reconfigure_jenkins_jobs_params()


