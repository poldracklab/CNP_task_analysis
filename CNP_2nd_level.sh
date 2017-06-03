#!/bin/bash
#SBATCH --time=30:00:00
#SBATCH --mem=64GB
#SBATCH --qos=russpold
#SBATCH -p russpold
#SBATCH --output=logs/CNP.group.%a.txt
#SBATCH --error=logs/CNP.group.%a.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=16
#SBATCH --ntasks=5

source /oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/config.sh

singularity exec -B $OAK:$OAK $SINGULARITY python -s CNP_2nd_level.py --task=bart &
singularity exec -B $OAK:$OAK $SINGULARITY python -s CNP_2nd_level.py --task=scap &
singularity exec -B $OAK:$OAK $SINGULARITY python -s CNP_2nd_level.py --task=taskswitch &
singularity exec -B $OAK:$OAK $SINGULARITY python -s CNP_2nd_level.py --task=pamret &
singularity exec -B $OAK:$OAK $SINGULARITY python -s CNP_2nd_level.py --task=stopsignal &

wait

echo "༼ つ ◕_◕ ༽つ CNP group modeling finished"
