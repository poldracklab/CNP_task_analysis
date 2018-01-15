from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces import fsl
from utils import get_config
import nibabel as nib
import numpy as np
import argparse
import shutil
import os

parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
parser.add_argument('-task','--task',dest='task',help='task name',required=True)
parser.add_argument('-contrast','--contrast',dest='contrast',help='contrast number',required=True)
parser.add_argument('--experiment','--experiment',dest='experiment',help='experiment number',required=True)
args = parser.parse_args()

experiment = int(args.experiment)

#prep_pipeline = 'fmriprep-1.0.3'

##############################
# TAKE SAMPLE FOR EXPERIMENT #
##############################

# collect subjects

prepdir = os.environ.get("PREPBASEDIR")
fmriprepdir = os.path.join(prepdir,'fmriprep-1.0.3','fmriprep')
subjects = [x for x in os.listdir(fmriprepdir) if x[-4:]!='html' and x[:4]=='sub-']

subs = []
for subject in subjects:
    image = os.path.join(prepdir,'fmriprep-1.0.3','fmriprep',subject,'func',
                         '%s_task-%s_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'%(subject,args.task))
    if os.path.exists(image):
        subs.append(subject)

subs = set(subs)-set(['sub-50010','sub-11067','sub-10527'])
subjects = list(subs)

# take two subsamples

for samplesize in range(10,31):
    np.random.seed(experiment*samplesize)

    sampledsubjects = np.random.choice(len(subjects),samplesize*2,replace=False)
    sampledsubjects = [np.array(subjects)[sampledsubjects[:samplesize]].tolist(),
                       np.array(subjects)[sampledsubjects[samplesize:]].tolist()]

    print("##################################################")
    print("#            Sampled subjects:                   #")
    print("##################################################")
    print(", ".join(sampledsubjects[0]))
    print(", ".join(sampledsubjects[1]))
    print("##################################################")

    #################
    ## TEST-RETEST ##
    #################

    task = args.task
    contrast = int(args.contrast)

    # loop over pipelines

    for prep_pipeline in ['fmriprep-1.0.3','fslfeat_5.0.9']:

        cf = get_config.get_folders(prep_pipeline)
        featdir = cf['resdir']
        groupdir = cf['groupdir']

        # create folder for samplesize
        ssdir = os.path.join(groupdir,"samplesize_%i"%samplesize)
        if not os.path.exists(ssdir):
            os.mkdir(ssdir)

        # create folder for experiment

        outdir = os.path.join(ssdir,"experiment_%i"%experiment)
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        # create subfolder with task

        outtaskdir = os.path.join(outdir,task)
        if not os.path.exists(outtaskdir):
            os.mkdir(outtaskdir)

        dims = [65,77,49] if prep_pipeline.startswith('fmriprep') else [97,115,97]

        #######################
        ## CREATE GROUP MASK ##
        #######################
        # this is being repeated now everytime, ugh

        groupmaskfile = os.path.join(outtaskdir,"mask.nii.gz")

        if not os.path.exists(groupmaskfile):
        #if True:
            prepdir = os.environ.get("PREPBASEDIR")
            subjects = [x for x in os.listdir(featdir) if x[-4:]!='html' and x[:4]=='sub-']
            mask = np.zeros(dims+[len(subjects)])
            k=0
            for subject in subjects:
                cf_files = get_config.get_files(prep_pipeline,subject,task)
                maskfile = cf_files['standard_mask']
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

        for sample in range(2):
            print("Starting Sample %i"%sample)

            featdirs = []
            for sub in sampledsubjects[sample]:
                subfeatdir = os.path.join(featdir,sub,"%s.feat"%task)
                if not os.path.exists(subfeatdir):
                    print("subject not found: %s"%sub)
                else:
                    featdirs.append(subfeatdir)

            # create folders

            sampledir = os.path.join(outtaskdir,"sample_%i"%sample)
            if not os.path.exists(sampledir):
                os.mkdir(sampledir)
            outcopedir = os.path.join(outtaskdir,"sample_%i"%sample,"cope%i"%(contrast))
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
            # randdir = os.path.join(basedir,'randomise')
            # if not os.path.exists(randdir):
            #     os.mkdir(randdir)

            # randomise_cmd = 'randomise -i %s/copemerge/cope%i_merged.nii.gz -o %s/randomise -d %s/l2model/design.mat -t %s/l2model/design.con -c 3.1 -v 5 -C 3.1 -m %s -n 500 -T -x --uncorrp'%(basedir,contrast,basedir,basedir,basedir,groupmaskfile)
            # os.popen(randomise_cmd).read()

            # remove unwanted files

            for analysis in ['flame1','OLS','randomise']:
                if analysis == "randomise":
                    continue #(not running)
                    # destdir = os.path.join(outcopedir,analysis)
                    # if not os.path.exists(destdir):
                    #     os.mkdir(destdir)
                    # for suffix in ['_tfce_corrp_tstat1.nii.gz','_tstat1.nii.gz','_clustere_corrp_tstat1.nii.gz','_clusterm_corrp_tstat1.nii.gz','_vox_corrp_tstat1.nii.gz', '_vox_p_tstat1.nii.gz']:
                    #     source = os.path.join(basedir,'randomise%s'%suffix)
                    #     destination = os.path.join(destdir,'randomise%s'%suffix)
                    #     shutil.move(source,destination)
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
            # destdir = os.path.join(outcopedir,"randomise")
            # if not os.path.exists(destdir):
            #     os.mkdir(destdir)
            #
            # os.chdir(destdir)
            # fdrcmd = 'fdr -i randomise_vox_p_tstat1 --oneminusp -m %s -q 0.05 --othresh=thresh_vox_fdr_pstat1'%(groupmaskfile)
            # os.popen(fdrcmd).read()
            # fwecmd = 'fslmaths randomise_vox_corrp_tstat1.nii.gz -thr 0.95 -bin -mul randomise_tstat1 thresh_vox_fwe_tstat1'
            # os.popen(fwecmd).read()
            # clucmd = 'fslmaths randomise_clustere_corrp_tstat1.nii.gz -thr 0.95 -bin -mul randomise_tstat1 thresh_cluster_fwe_tstat1'
            # os.popen(clucmd).read()
