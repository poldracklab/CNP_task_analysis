#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=32GB
##SBATCH --qos=russpold
##SBATCH -p russpold
#SBATCH --output=logs/CNP.%a.txt
#SBATCH --error=logs/CNP.%a.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=8
#SBATCH --ntasks=1

source /oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/config.sh

unset PYTHONPATH

singularity exec $SINGULARITY echo "Analyis '${SLURM_ARRAY_TASK_ID}' started"

set -e

eval $( sed "${SLURM_ARRAY_TASK_ID}q;d" tasks.txt )

echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
