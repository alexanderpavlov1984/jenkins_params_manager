import jenkins
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
import yaml
from yaml.loader import SafeLoader
import re


server = jenkins.Jenkins('http://51.250.87.0:8080/', username='pavlovas', password='c6f31c15976a4960bb5dc33542a8d0b7')
job_conf_xml = server.get_job_config('jenkins_params_manager')
print(job_conf_xml)
