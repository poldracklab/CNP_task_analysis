import os

bids = os.environ.get("BIDSDIR")
home = os.environ.get("HOMEDIR")

jobsfile = os.path.join(home,"hpc/tasks.txt")
if os.path.exists(jobsfile):
    os.remove(jobsfile)

subjects = [x for x in os.listdir(bids) if 'sub-' in x]

for prep_pipeline in ['fmriprep','feat']:
    for subject in subjects:
        cmd = "singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_analysis.py --subject=%s --prep_pipeline=%s"%(subject,prep_pipeline)
        with open(jobsfile,'a') as f:
            f.write(cmd+"\n")
