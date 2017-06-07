#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=64GB
#SBATCH --output=logs/CNP.ACM.txt
#SBATCH --error=logs/CNP.ACM.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1

source /oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/config.sh
module load singularity

unset PYTHONPATH

if [ ! -f $SINGULARITY ]; then
    echo "Singularity container for analyses not found!  Please first create singularity container."
fi

singularity exec $SINGULARITY echo "Analyis '${SLURM_ARRAY_TASK_ID}' started"

cd $HOMEDIR

set -e

singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=scap & \
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=taskswitch & \
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=stopsignal & \
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=pamret & \
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=bart & \

wait


echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
