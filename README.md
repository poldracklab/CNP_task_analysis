# CNP task analysis

This repository contains the code to analyse the CNP task data ([ds_000030, available on openfmri.org](https://openfmri.org/dataset/ds000030/)).  

### Reproducibility

The only dependency to re-run these analyses is **singularity 2.3**.

The analyses have been run in a [singularity](http://singularity.lbl.gov/) container, based on a [docker](https://www.docker.com/) container.  The docker container is publicly available on [docker hub](https://hub.docker.com/r/poldracklab/cnp_task_analysis/).

On a machine that has docker installed, the singularity container can be obtained by running:

```
docker run -v /var/run/docker.sock:/var/run/docker.sock -v /local:/output --privileged -t --rm singularityware/docker2singularity poldracklab/cnp_task_analysis:1.0
```

After running this command, the singularity container can be found in the `/local` folder on the local machine.

### Machine and data configuration

The data is assumed to be structured in [BIDS](bids.neuroimaging.io) format and preprocessed using [fmriprep](http://fmriprep.readthedocs.io/en/stable/).  All configuration (loading singularity, referencing data and code paths) is specified in `config.sh`.

### File structure

```
+-- hpc/                            Folder with scripts used to submit and run jobs
|    |                              on a HPC environment with a SLURM scheduler.
|    |
|    +-- 01_prepare.sh              Script to prepare task files (each line = 1 task)
|    +-- 02_CNP_analysis.sh         Array job script that run the first level analyses.
|    +-- 03_CNP_2nd_level.sh        Array job script that runs the group analyses.
|    +-- 04_CNP_2nd_level_ACM.sh    Job script to compute the ACM's for all contrasts.
|    |
|    +-- write_contrasts.py         Python script to write json with contrast information.
|    |                              (called by 01_prepare.sh)
|    +-- write_tasks.py             Python script to write task files.
|    |                              (called by 01_prepare.sh)
|    +-- write_group_tasks.py       Python script to write task files.
|                                   (called by 01_prepare.sh)
+-- utils/
|    +-- utils.py                   Functions used in first level analyses.
|
+-- CNP_analysis.py                 Program to run first level analysis on 1 subject.
+-- CNP_2nd_level.py                Program to run group level analysis on 1 contrast
|                                   (and 1 task).
+-- CNP_2nd_level_ACM.py            Program to generate ACM's for all contrasts.
+-- CNP_group_figures.py            Program to write figures used in the accompanying
|                                   paper.
+-- config.sh                       configuration file setting environment variables
|                                   specifying the location of the data and code.
+-- Dockerfile                      File to create docker container. Autobuild on docker
                                    hub.
```
