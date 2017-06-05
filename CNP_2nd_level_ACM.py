import nibabel as nib
import numpy as np
import os
import argparse
from nipype.interfaces import fsl
from nipype.pipeline.engine import Workflow, Node, MapNode
import shutil
import json

featdir = os.environ.get("RESUDIR")
outdir = os.environ.get("GROUPDIR")
homedir = os.environ.get("HOMEDIR")
acmdir = os.environ.get("ACMDIR")

contrastfile = os.path.join(homedir,"utils/contrasts.json")

with open(contrastfile) as fl:
    contrasts = json.load(fl)

for task in contrasts.keys():
#for task in ['bart']

    acmtaskdir = os.path.join(acmdir,task)
    if not os.path.exists(acmtaskdir):
        os.mkdir(acmtaskdir)

    groupmaskfile = os.path.join(os.path.join(outdir,task),"mask.nii.gz")

    for contrast in range(len(contrasts[task])):

        ##############################
        ## COLLECT FEAT DIRECTORIES ##
        ##############################

        featdirs = []
        for sub in os.listdir(featdir):
            if sub[:4]!= 'sub-':
                continue
            subfeatdir = os.path.join(featdir,sub,"%s.feat"%task)
            if os.path.exists(subfeatdir):
                featdirs.append(subfeatdir)

        ################
        ## create ACM ##
        ################

        zstats = [os.path.join(x,'stats','%s%i.nii.gz'%('zstat',contrast+1)) for x in featdirs]

        ACM = np.zeros([65,77,49,len(zstats)])
        for idx,zstat in enumerate(zstats):
            zmap = nib.load(zstat).get_data()
            exceed = np.where(zmap>1.65)
            ACM[exceed[0],exceed[1],exceed[2],idx] = 1

        ACM = np.mean(ACM,axis=3)

        ACMfile = os.path.join(acmtaskdir,"zstat%i_ACM.nii.gz"%(contrast+1))
