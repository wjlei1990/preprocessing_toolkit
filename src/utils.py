from __future__ import division, print_function
import os
import glob
import yaml
import math
import shutil
import fileinput
import sys


def dump_list(values, filename):
    with open(filename, "w") as fh:
        for v in values:
            fh.write("%s\n" % v)


def read_txt(filename):
    with open(filename) as fh:
        return [line.strip() for line in fh]


def read_yaml(filename):
    with open(filename) as fh:
        return yaml.load(fh)


def copy_param_files(taglist, inputbase, outputbase):
    outputdir = os.path.join(outputbase, "params")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for tag in taglist:
        inputfile = os.path.join(inputbase, "%s.param.yml" % tag)
        shutil.copy(inputfile, outputdir)


def copy_path_files(eventlist, taglist, inputbase, outputbase):
    outputdir = os.path.join(outputbase, "paths")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for event in eventlist:
        for tag in taglist:
            inputfile = os.path.join(inputbase, "%s.%s.path.json"
                                     % (event, tag))
            shutil.copy(inputfile, outputdir)


def split_job(eventlist, nevents_per_job):
    """
    split eventlist according to nevents_per_job
    """
    print("="*20)
    print("total number of events: %d" % len(eventlist))
    njobs = int(math.ceil(len(eventlist) / float(nevents_per_job)))
    joblist = {}
    for idx in range(njobs):
        start_idx = idx * nevents_per_job
        end_idx = (idx + 1) * nevents_per_job
        joblist[idx] = eventlist[start_idx:end_idx]

    print("nevents per job: %d" % nevents_per_job)
    print("njobs splitted: %d" % njobs)
    return joblist


def dump_cmtlist(cmtlist_per_job, outputdir):
    for idx, cmtlist in enumerate(cmtlist_per_job):
        outputfile = os.path.join(outputdir, "cmtlist.%d" % idx)
        dump_list(cmtlist, outputfile)


def clean_outputdir(outputdir, remove_list=["*.bash", "*.py", "cmtlist.*"]):
    if os.path.exists(outputdir):
        print("Output dir exists: %s" % outputdir)
        answer = raw_input("Removed[Y/n]:")
        if answer == "Y":
            shutil.rmtree(outputdir)
        elif answer == "n":
            print("Outputdir is not removed...Quit")
            sys.exit(1)
        else:
            raise ValueError("Please anwser 'Y' or 'n'")
        for _type in remove_list:
            files = glob.glob(os.path.join(outputdir, _type))
            for _file in files:
                os.remove(_file)
    else:
        os.makedirs(outputdir)
