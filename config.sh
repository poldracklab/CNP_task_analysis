module load system
module load singularity/2.3

## INPUT

# location of the BIDS dataset
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3/
# location of the preprocessed data
export PREPDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/fmriprep/

## OUTPUT

# location of single subject analyses
export RESUDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task/
# location of group analyses
export GROUPDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task_group/
# location of ACM's
export ACMDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task_ACM/

## CODE

# location of this repository :-)
export HOMEDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/

## SINGULARITY CONTAINER

export SINGULARITY=$SCRATCH/CNP/poldracklab_cnp_task_analysis-2017-06-03-1246c19080c1.img
