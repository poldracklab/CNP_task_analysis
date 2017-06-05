module load system
module load singularity/2.3

export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3/
export PREPDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/fmriprep/
export RESUDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task/
export GROUPDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task_group/
export ACMDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task_ACM/
export HOMEDIR=/oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/
export SINGULARITY=$SCRATCH/CNP/poldracklab_cnp_task_analysis-2017-06-03-1246c19080c1.img
