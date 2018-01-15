import sys
import os

def get_folders(prep_pipeline):
    basedir = os.path.join(os.environ.get("PREPBASEDIR"),'fmriprep_vs_feat',prep_pipeline)
    if not os.path.exists(basedir):
        os.mkdir(basedir)

    cf = {
        'prepdir':os.path.join(os.environ.get('PREPBASEDIR'),prep_pipeline),
        'resdir':os.path.join(basedir,'task'),
        'groupdir':os.path.join(basedir,'task_group'),
        'acmdir':os.path.join(basedir,'task_acm'),
        'figdir':os.path.join(basedir,'task_figures'),
        'condir':os.path.join(basedir,'conmaps')
    }

    for k,v in cf.iteritems():
        if not os.path.exists(v):
            os.mkdir(v)

    return cf

def get_files(prep_pipeline,SUBJECT,TASK):
    folders = get_folders(prep_pipeline)
    if prep_pipeline.startswith('fmriprep'):
        cf = {
            'bold':os.path.join(folders['prepdir'],'fmriprep', SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_preproc.nii.gz"),
            'masked':os.path.join(folders['resdir'],SUBJECT,"preprocessed_masked.nii.gz"),
            'standard_mask':os.path.join(folders['prepdir'],'fmriprep',  SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz"),
            'smoothed':os.path.join(folders['resdir'],SUBJECT,"preprocessed_smooth.nii.gz"),
            'confoundsfile': os.path.join(folders['prepdir'],'fmriprep',  SUBJECT, 'func', SUBJECT + "_task-" + TASK + '_bold_confounds.tsv')
        }
    else:
        cf = {
            'bold':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'filtered_func_data.nii.gz'),
            'masked':os.path.join(folders['resdir'],SUBJECT,'filtered_func_masked.nii.gz'),
            'mask':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'mask.nii.gz'),
            'smoothed':os.path.join(folders['resdir'],SUBJECT,'filtered_func_smoothed.nii.gz'),
            'confoundsfile':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'mc','prefiltered_func_data_mcf.par'),
            'warpfile':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'reg','example_func2standard_warp.nii.gz'),
            'standard':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'reg','standard.nii.gz'),
            'standard_mask':os.path.join(folders['prepdir'],"%s.feat"%SUBJECT,'reg','standard_mask.nii.gz')
        }
    return cf
