import os

bids = os.environ.get("BIDSDIR")
home = os.environ.get("HOMEDIR")

jobsfile = os.path.join(home,"hpc/tasks.txt")
if os.path.exists(jobsfile):
    os.remove(jobsfile)

subjects = [x for x in os.listdir(bids) if 'sub-' in x]

for subject in subjects:
    cmd = "singularity exec $SINGULARITY python -s $HOMEDIR/CNP_analysis.py --subject=%s"%subject
    with open(jobsfile,'a') as f:
        f.write(cmd+"\n")
