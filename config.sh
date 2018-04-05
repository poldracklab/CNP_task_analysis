if [ $SHERLOCK = 2 ]
    then
        module load system
    fi

module load singularity

# location of the BIDS dataset
export BIDSDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3/
# location of the preprocessed data
export PREPBASEDIR=/oak/stanford/groups/russpold/data/ds000030/1.0.3/derivatives/

# location of this repository :-)
export HOMEDIR=$HOME/CNP_task_analysis/

## SINGULARITY CONTAINER
export SINGULARITY=$SINGULARITY_BIN/poldracklab_cnp-2018-04-05-7fa7069182f3.img

