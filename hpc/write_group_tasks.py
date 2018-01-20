import json
import os

home = os.environ.get("HOMEDIR")

jobsfile = os.path.join(home,"hpc/group_tasks.txt")
if os.path.exists(jobsfile):
    os.remove(jobsfile)

contrastfile = os.path.join(os.environ.get('HOMEDIR'),"utils/contrasts.json")
with open(contrastfile) as fl:
    contrasts = json.load(fl)

tasks = ['stopsignal']
contrasts = [len(contrasts[x]) for x in tasks]

firsts = []
k = 0
for experiment in range(400):
    for idx,task in enumerate(tasks):
        for con in [10]:
            k+=1
            cmd = "singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/CNP_2nd_level.py --task=%s --contrast=%i --experiment=%i"%(task,con+1,experiment)
            with open(jobsfile,'a') as f:
                f.write(cmd+"\n")
