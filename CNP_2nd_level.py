import nibabel as nib
import numpy as np
import os
import argparse
from nipype.interfaces import fsl
from nipype.pipeline.engine import Workflow, Node, MapNode
import shutil

featdir = os.environ.get("RESUDIR")
outdir = os.environ.get("GROUPDIR")

parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
parser.add_argument('-task','--task',dest='task',help='task name',required=True)
parser.add_argument('-contrast','--contrast',dest='contrast',help='contrast number',required=True)
args = parser.parse_args()

task = args.task
contrast = int(args.contrast)

outtaskdir = os.path.join(outdir,task)
if not os.path.exists(outtaskdir):
    os.mkdir(outtaskdir)

#######################
## CREATE GROUP MASK ##
#######################

groupmaskfile = os.path.join(outtaskdir,"mask.nii.gz")

if not os.path.exists(groupmaskfile):
    prepdir = os.environ.get("PREPDIR")
    subjects = [x for x in os.listdir(featdir) if x[-4:]!='html' and x[:4]=='sub-']
    mask = np.zeros([65,77,49,len(subjects)])
    k=0
    for subject in subjects:
        maskfile = os.path.join(prepdir,subject,'func',subject+"_task-"+task+"_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz")
        if os.path.exists(maskfile):
            masksub = nib.load(maskfile)
            data = masksub.get_data()
            mask[:,:,:,k] = data
            k += 1

    mask = mask[:,:,:,:k]

    mask = np.mean(mask,axis=3)
    mask = np.where(mask>0.8,1,0)
    maskimg = nib.Nifti1Image(mask,affine=masksub.get_affine(),header=masksub.get_header())
    maskimg.to_filename(groupmaskfile)

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

#########################
## LOOP OVER CONTRASTS ##
#########################

outcopedir = os.path.join(outtaskdir,"cope%i"%(contrast))
if not os.path.exists(outcopedir):
    os.mkdir(outcopedir)
copes = [os.path.join(x,'stats','%s%i.nii.gz'%('cope',contrast)) for x in featdirs]
varcopes = [os.path.join(x,'stats','%s%i.nii.gz'%('varcope',contrast)) for x in featdirs]

# define nodes

copemerge = Node(interface=fsl.Merge(
    dimension='t',
    in_files=copes),
    name='copemerge')
varcopemerge = Node(interface=fsl.Merge(
    dimension='t',
    in_files=varcopes),
    name='varcopemerge')
level2model = Node(interface=fsl.L2Model(
    num_copes=len(copes)),
    name='l2model')
OLS=Node(interface=fsl.FLAMEO(
    run_mode='ols',
    mask_file=groupmaskfile),
    name='OLS')
FLAME=Node(interface=fsl.FLAMEO(
    run_mode='flame1',
    mask_file=groupmaskfile),
    name='flame1')
# this part doesn't work in nipipe; a fix has been proposed
# randomise=Node(interface=fsl.Randomise(
#     mask = groupmaskfile,
#     vox_p_values = True,
#     num_perm=100,
#     c_thresh = 3.1,
#     cm_thresh = 3.1,
#     tfce=True),
#     name='randomise')

# create workflow

CNPgroup = Workflow(name='cnp_group')
CNPgroup.base_dir = outcopedir
CNPgroup.connect([(copemerge,OLS,[('merged_file','cope_file')]),
                (varcopemerge,OLS,[('merged_file','var_cope_file')]),
                (level2model,OLS,[('design_mat','design_file'),
                                  ('design_con','t_con_file'),
                                  ('design_grp','cov_split_file')]),
                (copemerge,FLAME,[('merged_file','cope_file')]),
                (varcopemerge,FLAME,[('merged_file','var_cope_file')]),
                (level2model,FLAME,[('design_mat','design_file'),
                                    ('design_con','t_con_file'),
                                    ('design_grp','cov_split_file')])
                # (copemerge,randomise,[('merged_file','in_file')]),
                # (level2model,randomise,[('design_mat','design_mat'),
                #                         ('design_con','tcon')]),
                ])

CNPgroup.write_graph(graph2use='colored')
CNPgroup.run('MultiProc', plugin_args={'n_procs': 4})

# manual randomise

basedir = os.path.join(outcopedir,"cnp_group")
randomise_cmd = 'randomise -i %s/copemerge/cope%i_merged.nii.gz -o %s/randomise -d %s/l2model/design.mat -t %s/l2model/design.con -c 3.1 -C 3.1 -m %s -n 10000 -T -x --uncorrp'%(basedir,contrast,basedir,basedir,basedir,groupmaskfile)
#os.popen(randomise_cmd).read()

# remove unwanted files

for analysis in ['flame1','OLS','randomise']:
    if analysis == "randomise":
        # continue
        destdir = os.path.join(outcopedir,analysis)
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        for suffix in ['_tfce_corrp_tstat1.nii.gz','_tstat1.nii.gz','_clustere_corrp_tstat1.nii.gz','_clusterm_corrp_tstat1.nii.gz','_vox_corrp_tstat1.nii.gz', '_vox_p_tstat1.nii.gz']:
            source = os.path.join(basedir,'randomise%s'%suffix)
            destination = os.path.join(destdir,'randomise%s'%suffix)
            shutil.move(source,destination)
    else:
        resultdir = os.path.join(basedir,analysis,"stats")
        destdir = os.path.join(outcopedir,analysis)
        shutil.move(resultdir, destdir)

shutil.rmtree(basedir)

##################
## THRESHOLDING ##
##################

for analysis in ['flame1','OLS']:

    destdir = os.path.join(outcopedir,analysis)
    os.chdir(destdir)

    # FDR
    os.popen('fslmaths zstat1 -ztop pstat1').read()
    logpcmd = 'fdr -i pstat1 -m mask -q 0.05'
    thres = float(os.popen(logpcmd).read().split('\n')[1])
    threscmd = 'fslmaths pstat1 -mul -1 -add 1 -thr %f -mas mask thresh_vox_fdr_pstat1'%(1-thres)
    os.popen(threscmd).read()

    #FWE
    smoothcmd = 'smoothest -r res4d -d %i -m mask'%(len(featdirs)-1)
    smooth = os.popen(smoothcmd).read().split("\n")
    smoothn = [x.split(' ')[1] for x in smooth[:-1]]
    reselcount = float(smoothn[1])/float(smoothn[2])
    fwethrescmd = 'ptoz 0.05 -g %f'%reselcount
    fwethres = os.popen(fwethrescmd).read().split("\n")[0]
    fwecmd = 'fslmaths zstat1 -thr %s thresh_vox_fwe_zstat1'%fwethres
    fwe = os.popen(fwecmd).read()

    # cluster extent
    clustercmd = 'cluster -i zstat1 -c cope1 -t 3.2 -p 0.05 -d %s --volume=%s --othresh=thresh_cluster_fwe_zstat1 --connectivity=26 --mm'%(smoothn[0],smoothn[1])
    clusterout = os.popen(clustercmd).read()
    f1=open('thres_cluster_fwe_table.txt','w+')
    f1.write(clusterout)

#### randomise
destdir = os.path.join(outcopedir,"randomise")
os.chdir(destdir)
fdrcmd = 'fdr -i randomise_vox_p_tstat1 --oneminusp -m %s -q 0.05 --othresh=thresh_vox_fdr_pstat1'%(groupmaskfile)
os.popen(fdrcmd).read()
fwecmd = 'fslmaths randomise_vox_corrp_tstat1.nii.gz -thr 0.95 -bin -mul randomise_tstat1 thresh_vox_fwe_tstat1'
os.popen(fwecmd).read()
clucmd = 'fslmaths randomise_clustere_corrp_tstat1.nii.gz -thr 0.95 -bin -mul randomise_tstat1 thresh_cluster_fwe_tstat1'
os.popen(clucmd).read()
