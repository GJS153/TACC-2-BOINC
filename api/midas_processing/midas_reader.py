"""
BASICS

Analyzes the MIDAS README and draws conclusions.
Deals with finding the OS and the languages used
"""

import os


# Finds the corresponding image to the OS
OS_chart = {'Ubuntu_16.04':'carlosred/ubuntu-midas:16.04'}
# Python refers to python3 by default, python2 is not supported
Allowed_languages = ['python', 'r', 'c', 'c++', 'haskell', 'fortran']




# Verifies that a file has all 5 required inputs
# README_path (str): Must be the full path to the README
def valid_README(README_path):
	
    qualifier = [['OS)', 'LANGUAGE)', 'COMMAND)', 'OUTPUT)'], [0, 0, 0, 0]]

    for nvnv in range(0, len(qualifier[0])):
        with open(README_path, 'r') as README:
            for line in README:
                if qualifier[0][nvnv] in line:
                    qualifier[1][nvnv] = 1
                    break

    if 0 in qualifier[1]:
        return False
    return True


# Finds the OS
def valid_OS(README_path):

    with open(README_path, "r") as README:
        for line in README:
            # Only one OS is needed
            for onos in OS_chart.keys():
                if onos in line:
                    return onos
        
    # OS must be specified
    return False


# Finds the language(s)
def valid_language(README_path):

    lang_used = []
    with open(README_path, 'r') as README:
        for line in README:
            LLL = line.replace('\n', '').lower()
            for lang in Allowed_languages:
                if lang in LLL:
                    lang_used.append(lang)

        if len(lang_used) == 0:
            return False

        return lang_used


# Finds all the input files
# FILES_PATH (str): Path to all the files, inclusing the readme
def present_input_files(FILES_PATH):
    files_needed = os.listdir(FILES_PATH)
    files_present = []

    with open(FILES_PATH+"/README.txt", 'r') as README:
        for line in README:
            if "COMMAND)" not in line:
                continue

            LLL = line.replace("COMMAND)", '').replace('\n', '').replace(' ', '')
            files_present.append(LLL.split(':')[-1])

            if files_present[-1] not in files_needed:
                return False

    return files_present
            