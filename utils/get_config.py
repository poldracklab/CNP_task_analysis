import os


def get_folders(prep_pipeline, bids_dir=None):
    if bids_dir is None:
        bids_dir = os.environ.get('BIDSDIR')

    derivdir = os.environ.get("PREPBASEDIR",
                              os.path.join(bids_dir, 'derivatives'))
    basedir = os.path.join(derivdir, 'fmriprep_vs_feat_2.0-jd',
                           prep_pipeline)

    if not os.path.exists(basedir):
        os.makedirs(basedir)

    cf = {
        'prepdir': os.path.join(derivdir, prep_pipeline),
        'resdir': os.path.join(basedir, 'task'),
        'groupdir': os.path.join(basedir, 'task_group'),
        'acmdir': os.path.join(basedir, 'task_acm'),
        'figdir': os.path.join(basedir, 'task_figures'),
        'condir': os.path.join(basedir, 'conmaps')
    }

    for k, v in cf.iteritems():
        if not os.path.exists(v):
            os.makedirs(v)

    return cf


def get_files(prep_pipeline, sub_id, task_id):
    folders = get_folders(prep_pipeline)

    fmt = '{subject}_task-{task_id}_bold_{suffix}'.format
    prepfolder = folders['prepdir']

    if prep_pipeline.startswith('fmriprep'):
        prepfolder = os.path.join(prepfolder, 'fmriprep')

    if prep_pipeline.startswith('fslfeat'):
        prepfolder = os.path.join(prepfolder, 'featbids')

    cf = {
        'bold': os.path.join(prepfolder, sub_id, "func", fmt(
            subject=sub_id, task_id=task_id,
            suffix='space-MNI152NLin2009cAsym_preproc.nii.gz')),
        'mask': ('/oak/stanford/groups/russpold/data/'
                 'templates/mni_icbm152_nlin_asym_09c/2mm_brainmask.nii.gz'),
        'confoundsfile': os.path.join(prepfolder, sub_id, 'func', fmt(
            subject=sub_id, task_id=task_id, suffix='confounds.tsv')),
        'smoothed': os.path.join(folders['resdir'], sub_id, "preprocessed_smooth.nii.gz"),
        'masked': os.path.join(folders['resdir'], sub_id, "preprocessed_masked.nii.gz"),
        'standard_mask': ('/oak/stanford/groups/russpold/data/'
                          'templates/mni_icbm152_nlin_asym_09c/2mm_brainmask.nii.gz'),
    }
    return cf
