#!/usr/bin/env python
'''
Compiles a java or C source code and tests it with the inputs in a given folder
'''
import glob
import os
import plac
import subprocess
import sys
import tempfile
import threading

from Queue import Queue, Empty

#COMPILATION CONSTANTS
CPP_OPTS  = '-W -lm -g'

GPP = 'g++'
JAVA = 'java'
JAVAC = 'javac'
PYTHON = 'python'

def compile_python(source_code):
    '''Returns the command to run a python script'''

    return PYTHON, source_code

def compile_java(source_code):
    '''
    Compiles java code and returns the path to the command to jun the 
    code
    '''

    tmp_dir = tempfile.mkdtemp()
    compile_status = subprocess.call([JAVAC, source_code, '-d', tmp_dir])

    if compile_status != 0:
        return None

    class_file, _ = os.path.splitext(source_code)
    class_name = os.path.basename(class_file)
    return JAVA, '-cp', tmp_dir, class_name

def compile_cpp(source_code):
    '''Compiles C code and returns the executable'''

    tmp_dir = tempfile.mkdtemp()
    
    out_fpath = os.path.join(tmp_dir, 'run_me')
    cmd = [GPP, source_code] + CPP_OPTS.split() + ['-o', out_fpath]

    compile_status = subprocess.call(cmd)

    if compile_status != 0:
        return None

    return out_fpath

def popen(cmd, input_file, exp_output_file):
    '''Creates a new process to execute the cmd'''

    tmp_dir = tempfile.mkdtemp()
    output_file = os.path.join(tmp_dir, 'out')

    run_status = 1
    with open(input_file) as in_stream, \
          open(output_file, 'w') as out_stream:
        proc = subprocess.Popen(cmd, stdin=in_stream, stdout=out_stream,
                                universal_newlines=True)

    return proc, output_file

def check_output(output_file, exp_output_file):
    '''Compares the expected output with the one produced by the code'''

    exp = []
    with open(exp_output_file) as expected:
        for line in expected:
            strp = line.strip()
            if len(strp) > 0:
                spl = strp.split()
                exp.append(frozenset(spl))

    act = []
    with open(output_file) as out:
        for line in out:
            strp = line.strip()
            if len(strp) > 0:
                spl = strp.split()
                act.append(frozenset(spl))

    return len(act) > 0 and act == exp

def run_one(cmd, input_file, exp_output_file, time_limit=10):
    '''Runs one test case returning 1 if passed and 0 otherwise'''

    proc, output_file = popen(cmd, input_file, exp_output_file)
    queue = Queue()

    def thread_run():
        print >>sys.stderr, 'Running:', cmd, 'in=', input_file, 'out=', exp_output_file
        proc.wait()
        queue.put(object())

    runner = threading.Thread(target=thread_run)
    runner.start()
    
    #If the process runs within the time limit, then we cheack outputs
    try:
        queue.get(True, time_limit)
        executed = True
        print >> sys.stderr, 'Done'
    except Empty:
        print >> sys.stderr, 'Killed, TLE'
        executed = False
    finally:
        #Killing the processes should take care of the thread
        try:
            proc.kill()
            proc.wait()
            runner.join()
        except:
            pass    

    print >>sys.stderr, 'Diff: ', output_file, exp_output_file
    return_val = executed and check_output(output_file, exp_output_file)
    print >>sys.stderr, 'Final res', return_val
    return return_val

def run_all(source_code, tests_folder):
    '''Runs the source code in all test cases of a given folder'''
    
    #Compile the code
    LANGS={'.java':compile_java, '.c':compile_cpp, '.cpp':compile_cpp,
           '.cc':compile_cpp, '.py':compile_python}
    _, ext = os.path.splitext(source_code)
    cmd = LANGS[ext](source_code)


    #Run test cases
    ins = sorted(glob.glob(tests_folder + '/*.in'))
    outs = sorted(glob.glob(tests_folder + '/*.out'))

    assert len(ins) == len(outs)

    num_cases = len(ins)
    if cmd is None:
        return num_cases, 0
    
    passed = 0
    for in_f, out_f in zip(ins, outs):
        print >>sys.stderr, 'Code under execution =', source_code
        passed += run_one(cmd, in_f, out_f)
        print >>sys.stderr
        print >>sys.stderr

    return num_cases, passed

if __name__ == '__main__':
    print plac.call(run_all)
