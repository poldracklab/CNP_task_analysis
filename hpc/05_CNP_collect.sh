#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=32GB
#SBATCH --qos=russpold
#SBATCH -p russpold
#SBATCH --output=logs/CNP.collect.txt
#SBATCH --error=logs/CNP.collect.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=1

source $HOME/CNP_analysis/config.sh
source /share/PI/russpold/software/setup_all.sh

python $HOMEDIR/collect_results.py

echo "༼ つ ◕_◕ ༽つ CNP collecting results finished"
