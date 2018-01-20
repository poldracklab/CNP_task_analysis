#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=32GB
#SBATCH --qos=russpold
#SBATCH -p russpold
#SBATCH --output=logs/CNP.ACM.txt
#SBATCH --error=logs/CNP.ACM.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1

source $HOME/CNP_analysis/config.sh

unset PYTHONPATH

if [ ! -f $SINGULARITY ]; then
    echo "Singularity container for analyses not found!  Please first create singularity container."
fi

singularity exec $SINGULARITY echo "Analyis started"

cd $HOMEDIR

set -e

singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=stopsignal  --prep_pipeline=fmriprep-1.0.3 & \
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=stopsignal  --prep_pipeline=fslfeat_5.0.9 & \

wait


echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
