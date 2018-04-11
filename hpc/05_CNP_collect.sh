#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=32GB
#SBATCH -p russpold,normal,owners,hns
#SBATCH -o logs/CNP-collect-%A.out
#SBATCH -e logs/CNP-collect-%A.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=<email>
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1

module load anaconda fsl
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3
export PREPBASEDIR=$BIDSDIR/derivatives
export HOMEDIR=$PWD/CNP_task_analysis

python -s $HOMEDIR/collect_results.py

echo "༼ つ ◕_◕ ༽つ CNP collecting results finished"
