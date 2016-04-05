from __future__ import division, print_function
import os
import yaml
import math
import shutil
import fileinput
from utils import dump_list, read_txt, read_yaml, split_job, dump_cmtlist
from utils import clean_outputdir


def copy_template(outputdir):
    shutil.copy("_template/job_proc_obsd.bash", outputdir)
    shutil.copy("_template/job_proc_obsd_one_event.bash", outputdir)


def copy_job_script(template_dir, outputdir):
    origin_file = os.path.join(template_dir, "job_proc_obsd.bash")
    outfile = os.path.join(outputdir, "job_proc_obsd.bash")
    shutil.copy(origin_file, outfile)

    origin_file = os.path.join(template_dir, "job_proc_obsd_one_event.bash")
    outfile = os.path.join(outputdir,
                           "job_proc_obsd_one_event.bash")
    shutil.copy(origin_file, outfile)

    origin_file = os.path.join(template_dir, "process_asdf.py")
    outfile = os.path.join(os.path.dirname(outputdir),
                           "process_asdf.py")
    shutil.copy(origin_file, outfile)


def copy_param_files(taglist, inputbase, outputbase):
    print("Copy param files: [%s --> %s]" % (inputbase,outputbase))
    outputdir = os.path.join(outputbase, "params")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for tag in taglist:
        inputfile = os.path.join(inputbase, "%s.param.yml" % tag)
        shutil.copy(inputfile, outputdir)


def copy_path_files(eventlist, taglist, inputbase, outputbase):
    print("Copy path files: [%s --> %s]" % (inputbase, outputbase))
    outputdir = os.path.join(outputbase, "paths")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for event in eventlist:
        for tag in taglist:
            inputfile = os.path.join(inputbase, "%s.%s.path.json"
                                     % (event, tag))
            shutil.copy(inputfile, outputdir)


def prepare_job_scripts(cmtlist_per_job, config):
    print("="*20)
    print("Preparing job scripts")
    workdir = config["outputdir"]
    logdir = os.path.join(workdir, "log")
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    local_temp = os.path.join(workdir, "_temp")
    if not os.path.exists(local_temp):
        os.makedirs(local_temp)
    copy_job_script(config["job_template_dir"], local_temp)

    inputfile = os.path.join(local_temp, "job_proc_obsd_one_event.bash")
    outputfile = os.path.join(workdir, "job_proc_obsd_one_event.bash")
    nnodes_per_event = config["nnodes_per_event"]
    nprocs_per_node = config["nprocs_per_node"]
    nprocs = nnodes_per_event * nprocs_per_node
    modify_one_job_script(inputfile, nprocs, config["taglist"], outputfile)
    print("Number of nodes per event:%d" % nnodes_per_event)
    print("Number of procs per event:%d" % nprocs)

    walltime = config["job_running_time"]
    for job_idx, cmtlist in enumerate(cmtlist_per_job):
        nnodes = nnodes_per_event * len(cmtlist)
        inputfile = os.path.join(local_temp, "job_proc_obsd.bash")
        cmtlist_file = "cmtlist.%d" % job_idx
        outputfile = os.path.join(workdir, "job_proc_obsd.%d.bash" % job_idx)
        modify_job_script(inputfile, nnodes, walltime, cmtlist_file, job_idx,
                          outputfile)


def modify_job_script(inputfile, nnodes, walltime, cmtlist_file, job_idx,
                      outputfile):
    """
    Modify job_proc_obsd.bash
    """
    with open(inputfile) as fh:
        content = [ line.rstrip() for line in fh.readlines()]

    new = []
    for line in content:
        if line.startswith("#PBS -N"):
            line = "#PBS -N proc_obsd_%d" % job_idx
        if line.startswith("#PBS -l walltime="):
            line = "#PBS -l walltime=%s" % walltime
        if line.startswith("#PBS -l nodes="):
            line = "#PBS -l nodes=%s" % nnodes
        if line.startswith("eventfile="):
            line = "eventfile=\"%s\"" % cmtlist_file
        new.append(line)
    dump_list(new, outputfile)


def modify_one_job_script(inputfile, nprocs, taglist, outputfile):
    """
    Modify job_proc_obsd_one_event.bash
    """
    with open(inputfile) as fh:
        content = [ line.rstrip() for line in fh.readlines()]
    tag_content = ""
    # prepare tag list
    for tag in taglist:
        tag_content += "\"%s\" " % tag
    tag_content = "taglist=(%s)" % tag_content

    new = []
    for line in content:
        if line.startswith('taglist='):
            line = tag_content
        if line.startswith("numproc="):
            line = "numproc=%d" % nprocs
        new.append(line)
    dump_list(new, outputfile)


def prepare_proc_obsd(config):
    # mkdir outputbase
    outputbase = config["outputdir"]
    clean_outputdir(outputbase)

    # copy param files
    taglist = config["taglist"]
    copy_param_files(taglist, config["paramdir"], outputbase)

    # copy path files
    eventlist_file = config["eventlist"]
    eventlist = read_txt(eventlist_file)
    if len(eventlist) == 0:
        raise ValueError("No events found in file:" % eventlist_file)
    copy_path_files(eventlist, taglist, config["pathdir"], outputbase)

    # split the eventlist and dump into separate files
    nevents_per_job = config["nevents_per_job"]
    cmtlist_per_job = split_job(eventlist, nevents_per_job)
    dump_cmtlist(cmtlist_per_job, outputbase)

    # prepare job scripts
    prepare_job_scripts(cmtlist_per_job, config)


if __name__ == "__main__":

    config = read_yaml("config.yaml")
    prepare_proc_obsd(config)

