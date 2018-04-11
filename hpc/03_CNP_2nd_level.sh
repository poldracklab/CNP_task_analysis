#!/bin/bash
#SBATCH --array=1-200
#SBATCH -t 10:00:00
#SBATCH --mem=4G
#SBATCH -p russpold,owners,normal,hns
#SBATCH --output=logs/CNP-group-%A.%a.out
#SBATCH --error=logs/CNP-group-%A.%a.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>
#SBATCH --cpus-per-task=1

module load system
module load singularity

# source $HOME/CNP_task_analysis/config.sh
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis
unset PYTHONPATH

cmd=$( sed "${SLURM_ARRAY_TASK_ID}q;d" group_tasks.txt )

echo "Analysis ${SLURM_ARRAY_TASK_ID} started"
echo "Running: $cmd"
eval $cmd

echo "༼ つ ◕_◕ ༽つ CNP 2nd level pipeline (task ${SLURM_ARRAY_TASK_ID}) finished"

