from utils import get_config
import nibabel as nib
import numpy as np
import argparse
import shutil
import json
import os

parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
parser.add_argument('-task','--task',dest='task',help='task name',required=True)
parser.add_argument('-prep_pipeline','--prep_pipeline',dest='prep_pipeline',help='preprocessing pipeline',required=True)

args = parser.parse_args()

task = args.task

cf = get_config.get_folders(args.prep_pipeline)
featdir = cf['resdir']
outdir = cf['groupdir']
acmdir = cf['acmdir']

homedir = os.environ.get("HOMEDIR")

contrastfile = os.path.join(homedir,"utils/contrasts.json")

dims = [65,77,49] if args.prep_pipeline.startswith('fmriprep') else [97,115,97]

with open(contrastfile) as fl:
    contrasts = json.load(fl)

acmtaskdir = os.path.join(acmdir,task)
if not os.path.exists(acmtaskdir):
    os.mkdir(acmtaskdir)

groupmaskfile = os.path.join(os.path.join(outdir,task),"mask.nii.gz")
groupmask = nib.load(groupmaskfile).get_data()

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

    ACM_pos = np.zeros(dims+[len(zstats)])
    ACM_neg = np.zeros(dims+[len(zstats)])
    for idx,zstat in enumerate(zstats):
        zmap = nib.load(zstat).get_data()
        exceed = np.where(zmap>1.65)
        ACM_pos[exceed[0],exceed[1],exceed[2],idx] = 1
        exceed = np.where(zmap<-1.65)
        ACM_neg[exceed[0],exceed[1],exceed[2],idx] = 1

    ACM_pos = np.mean(ACM_pos,axis=3)
    ACM_pos = ACM_pos*groupmask
    ACM_neg = np.mean(ACM_neg,axis=3)
    ACM_neg = ACM_neg*groupmask

    ACM_diff = ACM_pos-ACM_neg

    zmap = nib.load(zstats[0])
    ACMfile = os.path.join(acmtaskdir,"zstat%i_ACM_pos.nii.gz"%(contrast+1))
    ACMimg = nib.Nifti1Image(ACM_pos,affine=zmap.get_affine(),header=zmap.get_header())
    ACMimg.to_filename(ACMfile)

    ACMfile = os.path.join(acmtaskdir,"zstat%i_ACM_neg.nii.gz"%(contrast+1))
    ACMimg = nib.Nifti1Image(ACM_neg,affine=zmap.get_affine(),header=zmap.get_header())
    ACMimg.to_filename(ACMfile)

    ACMfile = os.path.join(acmtaskdir,"zstat%i_ACM_diff.nii.gz"%(contrast+1))
    ACMimg = nib.Nifti1Image(ACM_diff,affine=zmap.get_affine(),header=zmap.get_header())
    ACMimg.to_filename(ACMfile)

    print("generated ACM for task %s, contrast %i"%(task,contrast))
