#!/bin/bash
#PBS -A GEO111
#PBS -N dsp_obsd
#PBS -j oe
#PBS -l walltime=NAN
#PBS -l nodes=NAN

# Signal processing
# ###################
eventfile="NAN"
# ###################

cd $PBS_O_WORKDIR
echo "Current dir:`pwd`"
echo "Time: `date`"
echo "Eventfile: $eventfile"

eventlist=`cat $eventfile`
idx=0
for event in ${eventlist[@]}
do
  echo "=============================="
  echo "Event: "$event
  bash job_dsp_one_event.$idx.bash $event &
  idx=$(($idx + 1))
done
wait

echo "Job done at: `date`"
echo "Number of events run: $idx"
