#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=8GB
#SBATCH -p hns,normal
##SBATCH --qos=russpold
##SBATCH -p russpold
#SBATCH --output=logs/CNP.%a.txt
#SBATCH --error=logs/CNP.%a.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=2
#SBATCH --ntasks=1

source $HOME/CNP_analysis/config.sh
# module load singularity

unset PYTHONPATH

if [ ! -f $SINGULARITY ]; then
    echo "Singularity container for analyses not found!  Please first create singularity container."
fi

singularity exec $SINGULARITY echo "Analysis '${SLURM_ARRAY_TASK_ID}' started"
cd $HOMEDIR
set -e
eval $( sed "${SLURM_ARRAY_TASK_ID}q;d" $HOMEDIR/hpc/tasks.txt )

echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
