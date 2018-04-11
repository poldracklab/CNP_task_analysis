#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=32GB
#SBATCH --qos=russpold
#SBATCH -p russpold
#SBATCH --output=logs/CNP.ACM.txt
#SBATCH --error=logs/CNP.ACM.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1
module load system
module load singularity

export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis
unset PYTHONPATH

singularity exec  $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=stopsignal  --prep_pipeline=fmriprep_1.0.8 & \
singularity exec  $SINGULARITY python -s $HOMEDIR/CNP_2nd_level_ACM.py --task=stopsignal  --prep_pipeline=fslfeat_5.0.10 & \

echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"
