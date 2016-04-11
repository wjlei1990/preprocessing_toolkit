#!/bin/bash
# ###################
pathdir="paths"
paramdir="params"
taglist=("NAN")
numproc=NAN
# ###################

eventname=$1

echo "Eventname: $eventname"

for tag in ${taglist[@]}
do
  pathfile=$pathdir"/"$eventname"."$tag".path.json"
  paramfile=$paramdir"/"$tag".param.yml"
  echo "event, pathfile, paramfile: $eventname, $pathfile, $paramfile"
  if [ ! -f $pathfile ]; then
    echo "PATH file not exists:$pathfile"
    exit
  fi
  if [ ! -f $paramfile ]; then
    echo "PARAM file not exists:$paramfile"
    exit
  fi

  logfile="log/"$eventname"."$tag".log"
  mpirun -n $numproc python window_selection_asdf.py \
    -p $paramfile \
    -f $pathfile \
    -v &> $logfile
done
