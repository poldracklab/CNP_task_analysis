if [ $SHERLOCK = 2 ]
    then
        module load system
        module load singularity/2.4
    fi
if [ $SHERLOCK = 1 ]
    then
        module load singularity
    fi

## INPUT

# location of the BIDS dataset
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3/
# location of the preprocessed data
export PREPBASEDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3/derivatives/

# location of this repository :-)
export HOMEDIR=$HOME/CNP_analysis/

## SINGULARITY CONTAINER
export SINGULARITY=$SCRATCH/poldracklab_cnp_task_analysis-2017-06-13-8a9da76ec6c3.img
