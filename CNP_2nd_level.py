import nibabel as nib
import numpy as np
import os
import argparse
from nipype.interfaces import fsl
from nipype.pipeline.engine import Workflow, Node, MapNode

featdir = os.environ.get("RESUDIR")
outdir = os.environ.get("GROUPDIR")

parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
parser.add_argument('-task','--task',dest='task',help='task name',required=True)
args = parser.parse_args()
task = args['task']

outtaskdir = os.path.join(outdir,task)
if not os.path.exists(outtaskdir):
    os.mkdir(outtaskdir)

#######################
## CREATE GROUP MASK ##
#######################

prepdir = os.environ.get("PREPDIR")
subjects = [x for x in os.listdir(featdir) if x[-4:]!='html' and x[:4]=='sub-']
mask = np.zeros([65,77,49,len(subjects)])
k=0
for subject in subjects:
    maskfile = os.path.join(prepdir,subject,'func',subject+"_task-"+task+"_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz")
    if os.path.exists(maskfile):
        data = nib.load(maskfile).get_data()
        mask[:,:,:,k] = data
        k += 1

mask = np.mean(mask,axis=3)
mask = np.where(mask>0.8,1,0)
groupmaskfile = os.path.join(outtaskdir,"mask.nii.gz")
maskimg = nib.Nifti1Image(mask,affine=nib.load(maskfile).get_affine(),header=nib.load(maskfile).get_header())
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

numcopes = len([x for x in os.listdir(os.path.join(featdirs[0],'stats')) if 'varcope' in x])

copes = []
varcopes = []
for contrast in range(numcopes):
    copes = [os.path.join(x,'stats','%s%i.nii.gz'%('cope',contrast+1)) for x in featdirs]
    varcopes = [os.path.join(x,'stats','%s%i.nii.gz'%('cope',contrast+1)) for x in featdirs]

    copemerge = Node(interface=fsl.Merge(
        dimension='t',
        in_files=copes),
        name='copemerge')
    varcopemerge = Node(interface=fsl.Merge(
        dimension='t',
        in_files=varcopes),
        name='varcopemerge')
    level2model = Node(interface=fsl.L2Model(
        num_copes=9),
        name='l2model')
    OLS=Node(interface=fsl.FLAMEO(
        run_mode='ols',
        mask_file=groupmaskfile),
        name='OLS')
    FLAME=Node(interface=fsl.FLAMEO(
        run_mode='flame1',
        mask_file=groupmaskfile),
        name='flame1')
    randomise=Node(interface=fsl.Randomise(
        mask = groupmaskfile,
        vox_p_values = True,
        num_perm=100,
        c_thresh = 3.09,
        tfce=True),
        name='randomise')

    CNPgroup = Workflow(name='cnp_group')
    CNPgroup.base_dir = outtaskdir
    CNPgroup.connect([(copemerge,OLS,[('merged_file','cope_file')]),
                    (level2model,OLS,[('design_mat','design_file'),
                                      ('design_con','t_con_file'),
                                      ('design_grp','cov_split_file')]),
                    (copemerge,FLAME,[('merged_file','cope_file')]),
                    (varcopemerge,FLAME,[('merged_file','var_cope_file')]),
                    (level2model,FLAME,[('design_mat','design_file'),
                                        ('design_con','t_con_file'),
                                        ('design_grp','cov_split_file')]),
                    (copemerge,randomise,[('merged_file','in_file')]),
                    (level2model,randomise,[('design_mat','design_mat'),
                                        ('design_con','tcon')]),
                    ])

    CNPgroup.write_graph(graph2use='colored')
    CNPgroup.run('MultiProc', plugin_args={'n_procs': 4})
