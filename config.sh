module load system
module load singularity/2.3

## INPUT

# location of the BIDS dataset
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3/
# location of the preprocessed data
export PREPBASEDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/

# location of this repository :-)
export HOMEDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/

## SINGULARITY CONTAINER
export SINGULARITY=$SCRATCH/poldracklab_cnp_task_analysis-2017-06-13-8a9da76ec6c3.img
