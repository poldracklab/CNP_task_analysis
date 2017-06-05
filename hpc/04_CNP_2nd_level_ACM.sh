#!/bin/bash
#SBATCH --time=30:00:00
#SBATCH --mem=16GB
#SBATCH --output=logs/CNP.group.%a.txt
#SBATCH --error=logs/CNP.group.%a.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=10
#SBATCH --ntasks=1
#SBATCH --qos=russpold
#SBATCH -p russpold

source /oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/config.sh
module laod singularity

unset PYTHONPATH

if [ ! -f $SINGULARITY ]; then
    echo "Singularity container for analyses not found!  Please first create singularity container."
fi

singularity exec $SINGULARITY echo "Analyis '${SLURM_ARRAY_TASK_ID}' started"

cd $HOMEDIR

set -e

singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py

echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
