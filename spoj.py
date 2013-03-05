#!/usr/bin/env python
'''
Script to submit solutions to SPOJ.
'''
from poster.encode import multipart_encode

import os
import plac
import re
import sys
import time
import tempfile
import urllib2

#URL CONSTANTS
BASE_URL = 'http://www.spoj.pl/submit/complete/'
RESULTS_URL = 'http://www.spoj.pl/status/%s/signedlist/'

#LANG CODES
C = 11
CPP = 41
JAVA = 10
PYTHON = 4

LANGS={'.java':JAVA, '.c':C, '.cpp':CPP, '.cc':CPP, '.py':PYTHON}

#FORM DATA
FRM_USER = 'login_user'
FRM_PASS = 'password'
FRM_FILE = 'subm_file'
FRM_LANG = 'lang'
FRM_PROB = 'problemcode'

#REGULAR EXPRS
ID_PATTERN = re.compile(r'.*?<input type="hidden" name="newSubmissionId" value="(\d+)"/>.*')

#LE CODE!
def sleep(slp_time=3):
    '''Sleep wrapper'''
    time.sleep(slp_time)

def fix_java(code_file):
    '''
    Creates a new java class source code with class name Main and file name 
    Main.java
    '''

    old_class_name = os.path.basename(code_file).replace(r'.java', '')
    
    #tmp dir
    tmp_dir = tempfile.mkdtemp()
    new_file = os.path.join(tmp_dir, 'Main.java')
    
    #write new file
    with open(code_file) as java_code, open(new_file, 'w') as new_code:
        for line in java_code:
            if 'class %s' %old_class_name in line:
                print >>new_code, line.replace(old_class_name, 'Main'),
            else:
                print >>new_code, line,

    return new_file, open(new_file, 'rb')

def get_lang(code_file):
    '''Get's the language code based on file extension'''

    _, ext = os.path.splitext(code_file)
    return LANGS[ext]

def get_submission_id(the_page):
    '''Parses the response HTML for the unique Spoj submission ID'''

    for line in the_page:
        match = ID_PATTERN.match(line)

        if match:
            return match.group(1)

    return -1

def get_answer(user_name, sub_id):
    '''Parses the results and gets the line with the submission status'''

    url = RESULTS_URL % user_name
    
    while True:
        sleep()
        req = urllib2.Request(url)
        for line in urllib2.urlopen(req):
            if sub_id in line and '??' not in line:
                return line[:-1]

@plac.annotations(problem_code='SPOJ problem code', code_file='Code to submit',
                  user_name='SPOJ user name', passwd='SPOJ password')
def submit(problem_code, code_file, user_name, passwd):

    assert os.path.exists(code_file)
    code_file = os.path.abspath(code_file)

    lang = get_lang(code_file)
    if lang != JAVA:
        file_content = open(code_file, 'rb')
    else:
        code_file, file_content = fix_java(code_file)

    form = {FRM_USER:user_name,
            FRM_PASS:passwd,
            FRM_FILE:file_content,
            FRM_LANG:lang,
            FRM_PROB:problem_code}

    data, headers = multipart_encode(form)

    data = ''.join(data)
    req = urllib2.Request(BASE_URL, data, headers)
    
    response = urllib2.urlopen(req)
    sub_id = get_submission_id(response)
    file_content.close()

    if sub_id == -1:
        raise Exception('Unable to Submit')
    
    return get_answer(user_name, sub_id)

if __name__ == '__main__':
    print plac.call(submit)
