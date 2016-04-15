#!/bin/bash
#PBS -A GEO111
#PBS -N adjoint
#PBS -j oe
#PBS -l walltime=NAN
#PBS -l nodes=NAN

# Calculate adjoint sources
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
  bash job_adjoint_one_event.bash &
  idx=$(($idx + 1))
done
wait

echo "Job done at: `date`"
echo "Number of events run: $idx"
