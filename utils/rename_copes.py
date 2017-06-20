from shutil import copyfile
import json
import os

with open(os.path.join(os.environ.get("HOMEDIR"),'utils/contrasts.json'),'r') as fp:
    contrasts  = json.load(fp)


tasks = ['bart','scap','stopsignal','taskswitch','pamret']
groupdir = os.environ.get("GROUPDIR")
desdir = os.environ.get("CONDIR")

for task in tasks:
    taskdir = os.path.join(desdir,task)
    if not os.path.exists(taskdir):
        os.mkdir(taskdir)
    for cope in range(len(contrasts[task])):
        originT = os.path.join(groupdir,task,'cope%i'%(cope+1),'randomise/randomise_tstat1.nii.gz')
        destT = os.path.join(taskdir,"%s_%s.nii.gz"%(task,contrasts[task][cope]))
        copyfile(originT,destT)
