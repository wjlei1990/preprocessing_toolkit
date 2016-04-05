from __future__ import division, print_function
import os
import yaml
import math
import shutil
import fileinput
from utils import dump_list, read_txt, read_yaml, split_job, dump_cmtlist
from utils import clean_outputdir, copy_param_files, copy_path_files
from pprint import pprint


def copy_job_script(template_dir, outputdir):
    origin_file = os.path.join(template_dir, "process_asdf.py")
    outfile = os.path.join(outputdir, "process_asdf.py")
    shutil.copy(origin_file, outfile)


def prepare_job_scripts(cmtlist, job_idx, workdir, config):
    # copy script to local temp
    #local_temp = os.path.join(workdir, "_temp")
    #if not os.path.exists(local_temp):
    #    os.makedirs(local_temp)
    template_dir = config["job_template_dir"]
    copy_job_script(template_dir, workdir)

    if config["job_mode"] == "serial":
        modify_scripts_for_serial_run(template_dir, workdir, cmtlist, job_idx,
                                      config)
    elif config["job_mode"] == "simultaneous":
        modify_scripts_for_simul_run(template_dir, workdir, cmtlist, job_idx,
                                     config)


def modify_scripts_for_serial_run(template_dir, workdir, cmtlist, job_idx,
                                  config):
    # modify script for one event
    inputfile = os.path.join(template_dir, "job_dsp_one_event.bash")
    nnodes_per_event = config["nnodes_per_event"]
    nprocs_per_node = config["nprocs_per_node"]
    nprocs = nnodes_per_event * nprocs_per_node
    outputfile = os.path.join(workdir, "job_dsp_one_event.bash")
    modify_one_event_script(inputfile, nprocs, config["taglist"],
                            outputfile)

    # modify script for one job
    time_per_event = config["job_running_time"]
    total_time = time_per_event * len(cmtlist)
    h, m = divmod(total_time, 60)
    walltime = "%d:%02d:00" % (h, m)
    nnodes = nnodes_per_event
    inputfile = os.path.join(template_dir, "job_dsp.bash")
    cmtlist_file = "cmtlist"
    outputfile = os.path.join(workdir, "job_dsp.bash")
    modify_job_script(inputfile, nnodes, walltime, cmtlist_file, job_idx,
                      outputfile, mode="serial")


def modify_scripts_for_simul_run(template_dir, workdir, cmtlist, job_idx,
                                 config):
    # modify script for one event
    inputfile = os.path.join(template_dir, "job_dsp_one_event.bash")
    nnodes_per_event = config["nnodes_per_event"]
    nprocs_per_node = config["nprocs_per_node"]
    nprocs = nnodes_per_event * nprocs_per_node
    for cmt_idx in range(len(cmtlist)):
        outputfile = os.path.join(workdir, "job_dsp_one_event.%d.bash"
                                  % cmt_idx)
        modify_one_event_script(inputfile, nprocs, config["taglist"],
                                outputfile)

    # modify script for one job
    time_per_event = config["job_running_time"]
    h, m = divmod(time_per_event, 60)
    walltime = "%d:%02d:00" % (h, m)
    nnodes = nnodes_per_event * len(cmtlist)
    inputfile = os.path.join(template_dir, "job_dsp.bash")
    cmtlist_file = "cmtlist"
    outputfile = os.path.join(workdir, "job_dsp.bash")
    modify_job_script(inputfile, nnodes, walltime, cmtlist_file, job_idx,
                      outputfile, mode="simultaneous")


def modify_job_script(inputfile, nnodes, walltime, cmtlist_file, job_idx,
                      outputfile, mode="simultaneous"):
    """
    Modify job_proc_obsd.bash
    """
    with open(inputfile) as fh:
        content = [ line.rstrip() for line in fh.readlines()]

    new = []
    for line in content:
        if line.startswith("#PBS -N"):
            line = "%s_%d" % (line.rstrip(), job_idx)
        if line.startswith("#PBS -l walltime="):
            line = "#PBS -l walltime=%s" % walltime
        if line.startswith("#PBS -l nodes="):
            line = "#PBS -l nodes=%s" % nnodes
        if line.startswith("eventfile="):
            line = "eventfile=\"%s\"" % cmtlist_file
        # modify for serial
        if mode == "serial":
            if line.startswith("  bash job_dsp_one_event"):
                line = "  bash job_dsp_one_event.bash $event"
            if line.startswith("wait"):
                line = "#wait"
        new.append(line)
    dump_list(new, outputfile)


def modify_one_event_script(inputfile, nprocs, taglist, outputfile):
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
        if line.startswith('taglist=("'):
            line = tag_content
        if line.startswith("numproc="):
            line = "numproc=%d" % nprocs
        new.append(line)
    dump_list(new, outputfile)


def prepare_one_job(job_id, cmtlist, config):
    outputbase = config["outputdir"]
    outputdir = os.path.join(outputbase, "job_dsp_%d" % job_id)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    print("job id:%3d -- ncmt: %3d -- dir: %s" % (job_id, len(cmtlist),
                                                   outputdir))
    cmtfile = os.path.join(outputdir, "cmtlist")
    dump_list(cmtlist, cmtfile)

    # copy param files to subdir
    taglist = config["taglist"]
    copy_param_files(taglist, config["paramdir"], outputdir)

    # copy path files
    if len(cmtlist) == 0:
        raise ValueError("No events found in file:" % eventlist_file)
    copy_path_files(cmtlist, taglist, config["pathdir"], outputdir)

    # prepare job scripts
    prepare_job_scripts(cmtlist, job_id, outputdir, config)

    # make log dir
    logdir = os.path.join(outputdir, "log")
    if not os.path.exists(logdir):
        os.makedirs(logdir)


def prepare_proc_synt(config):
    # mkdir outputbase
    outputbase = config["outputdir"]
    clean_outputdir(outputbase)

    eventlist_file = config["eventlist"]
    eventlist = read_txt(eventlist_file)
    # split the eventlist and dump into separate files
    nevents_per_job = config["nevents_per_job"]
    cmtlist_per_job = split_job(eventlist, nevents_per_job)
    print("-"*10 + "\nJob list:\n%s" % cmtlist_per_job)

    print("="*20 + "\nPreparing jobs...")
    for job_id, cmtlist in cmtlist_per_job.iteritems():
        prepare_one_job(job_id, cmtlist, config)



if __name__ == "__main__":

    config = read_yaml("config.yaml")
    prepare_proc_synt(config)

