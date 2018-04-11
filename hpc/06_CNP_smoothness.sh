#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=64GB
#SBATCH --qos=russpold
#SBATCH -p russpold
#SBATCH --output=logs/CNP.collect.txt
#SBATCH --error=logs/CNP.collect.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1

module load fsl/5.0.9 anaconda afni

export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis
python -s $HOMEDIR/CNP_smoothness.py

echo "༼ つ ◕_◕ ༽つ CNP collecting results finished"
