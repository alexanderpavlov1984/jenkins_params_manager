'''
Этот скрипт позволяет автоматизировать конфигурирование параметров задачь Jenkins.
Параметры вносятся в .yaml фаил(ы) в формате:

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

Скрипт переводит yaml в xml-структуру в формате Jenkins-API, добавляет служебные xml-элементы необходимые для Jenkins-API,
получает список задач с сервера Jenkins и устанавливает их параметры в соответствии с
параметрами из .yaml файла(в) в директории со скриптом.
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
import re

server = jenkins.Jenkins('http://51.250.0.232:8080/', username='pavlovas', password='c6f31c15976a4960bb5dc33542a8d0b7')

def generate_choise_params_xml_from_yaml_file(params_yaml_file):
    '''Takes in a params.yaml file, returns the xml string for the Jenkins job parameters.'''

    with open(params_yaml_file, 'r') as stream:
        try:
            # Converts yaml document to python object
            parameters_dic = yaml.load(stream, Loader=SafeLoader)
        except yaml.YAMLError as e:
            print(e)

    new_choice_parameter_definition = ''
    new_choice_parameter_definition += '<parameterDefinitions>\n'
    for key in parameters_dic.keys():
        if key[0:4] == 'name':
            if '</hudson.model.ChoiceParameterDefinition>' in new_choice_parameter_definition:
                new_choice_parameter_definition += '\n'
            new_choice_parameter_definition += '<hudson.model.ChoiceParameterDefinition>\n'
            new_choice_parameter_definition += f'  <name>{parameters_dic[key]}</name>\n'
            new_choice_parameter_definition += '  <choices class="java.util.Arrays$ArrayList">\n'
            new_choice_parameter_definition += '    <a class="string-array">\n'
        elif key[0:7] == 'choices':
            for param in parameters_dic[key]:
                new_choice_parameter_definition += f'    <string>{param}</string>\n'
            new_choice_parameter_definition += '    </a>\n'
            new_choice_parameter_definition += '  </choices>\n'
            new_choice_parameter_definition += '</hudson.model.ChoiceParameterDefinition>'
    new_choice_parameter_definition += '\n</parameterDefinitions>'

    return new_choice_parameter_definition

def generate_complete_xml_jenkins_params_from_yaml(job_name_str, params_yaml_file):
    '''Takes in a params.yaml file, returns the xml string for the Jenkins job full config.'''

    job_conf_xml = server.get_job_config(job_name_str)

    # generate a new job config.xml from the job params.yaml   
    root = ET.fromstring(job_conf_xml)

    parameters_definitions = root.find('properties').find('hudson.model.ParametersDefinitionProperty').find('parameterDefinitions')

    elements_to_remove = []
    for element in root.iter('hudson.model.ChoiceParameterDefinition'): 
        elements_to_remove.append(element)
    for element in elements_to_remove:
        parameters_definitions.remove(element)
    hudson_params_def = root.find('properties').find('hudson.model.ParametersDefinitionProperty')
    param_definitions = root.find('properties').find('hudson.model.ParametersDefinitionProperty').find('parameterDefinitions')
    hudson_params_def.remove(param_definitions)

    choices_xml = generate_choise_params_xml_from_yaml_file(params_yaml_file)
    choices_et = ET.fromstring(choices_xml) 
    hudson_params_def.append(choices_et)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    xml_modified = ElementTree.tostring(root, encoding='unicode')

    return xml_modified

def reconfigure_jenkins_jobs_params(parameters_yaml):
    jobs_list = server.get_jobs()
    for job in jobs_list:
        if job['_class'] == 'hudson.model.FreeStyleProject':
            new_job_conf = generate_complete_xml_jenkins_params_from_yaml(job['name'], parameters_yaml)
            server.reconfig_job(job['name'], new_job_conf)

reconfigure_jenkins_jobs_params('prod_wf_modules_redeploy.yaml')

