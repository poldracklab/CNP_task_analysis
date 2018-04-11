#!/bin/bash
#SBATCH -J cnp_jd_2
##SBATCH --array=1-514
#SBATCH --array=117,121,124,125
#SBATCH -t 12:00:00
#SBATCH -c 2
#SBATCH -n 1
#SBATCH --mem=8GB
#SBATCH -p russpold,owners,normal

#SBATCH -o logs/CNP-1stlevel-%A-%a.out
#SBATCH -e logs/CNP-1stlevel-%A-%a.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>

module load system
module load singularity

export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis
unset PYTHONPATH

cmd=$( sed "${SLURM_ARRAY_TASK_ID}q;d" tasks.txt )

echo "Analysis ${SLURM_ARRAY_TASK_ID} started"
echo "Running: $cmd"
cd $HOMEDIR
set -e
eval $cmd

echo "༼ つ ◕_◕ ༽つ CNP 1st level pipeline (task ${SLURM_ARRAY_TASK_ID}) finished"

