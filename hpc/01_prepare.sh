#!/bin/bash
#SBATCH --time=00:20:00
#SBATCH --mem=4GB
##SBATCH --qos=russpold
##SBATCH -p russpold
#SBATCH --output=$HOME/logs/CNP-prepararion.%J.out
#SBATCH --error=$HOME/logs/CNP-preparation.%J.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1

module load system
module load singularity

export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis
unset PYTHONPATH

set -e

echo "Analysis started"
singularity exec $SINGULARITY python -s $HOMEDIR/hpc/write_contrasts.py
singularity exec $SINGULARITY python -s $HOMEDIR/hpc/write_group_tasks.py
singularity exec $SINGULARITY python -s $HOMEDIR/hpc/write_tasks.py

echo "༼ つ ◕_◕ ༽つ CNP pipeline preparation finished"
