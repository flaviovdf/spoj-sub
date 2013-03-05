#!/usr/bin/env python

import execute
import glob
import os
import plac

@plac.annotations(code_folder='Students source codes folder', 
                  tests_folder='Local tests folder')
def main(code_folder, tests_folder):

    sub_folds = sorted(glob.glob(code_folder + '*/'))

    for sub_folder in sub_folds:
        files = glob.glob(sub_folder + '/*.java')
        files.extend(glob.glob(sub_folder + '/*.c'))
        files.extend(glob.glob(sub_folder + '/*.cc'))
        files.extend(glob.glob(sub_folder + '/*.cpp'))

        for file_path in files:
            print file_path,
            local_res = execute.run_all(file_path, tests_folder)
            local_grade = float(local_res[1]) / local_res[0]
            print local_grade

if __name__ == '__main__':
    plac.call(main)
