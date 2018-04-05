import os


def get_folders(prep_pipeline):
    basedir = os.path.join(os.environ.get("PREPBASEDIR"), 'fmriprep_vs_feat', prep_pipeline)
    if not os.path.exists(basedir):
        os.mkdir(basedir)

    cf = {
        'prepdir': os.path.join(os.environ.get('PREPBASEDIR'), prep_pipeline),
        'resdir': os.path.join(basedir, 'task'),
        'groupdir': os.path.join(basedir, 'task_group'),
        'acmdir': os.path.join(basedir, 'task_acm'),
        'figdir': os.path.join(basedir, 'task_figures'),
        'condir': os.path.join(basedir, 'conmaps')
    }

    for k, v in cf.iteritems():
        if not os.path.exists(v):
            os.mkdir(v)

    return cf


def get_files(prep_pipeline, sub_id, task_id):
    folders = get_folders(prep_pipeline)

    if prep_pipeline.startswith('fmriprep'):
        fmt = '{subject}_task-{task_id}_bold_{suffix}'.format
        cf = {
            'bold': os.path.join(folders['prepdir'], 'fmriprep', sub_id, "func", fmt(
                subject=sub_id, task_id=task_id,
                suffix='space-MNI152NLin2009cAsym_preproc.nii.gz')),
            'masked': os.path.join(folders['resdir'], sub_id, "preprocessed_masked.nii.gz"),
            'standard_mask': os.path.join(folders['prepdir'], 'fmriprep', sub_id, "func", fmt(
                subject=sub_id, task_id=task_id,
                suffix='space-MNI152NLin2009cAsym_brainmask.nii.gz')),
            'smoothed': os.path.join(folders['resdir'], sub_id, "preprocessed_smooth.nii.gz"),
            'confoundsfile': os.path.join(folders['prepdir'], 'fmriprep', sub_id, 'func', fmt(
                subject=sub_id, task_id=task_id, suffix='confounds.tsv')),
        }
    else:
        fmt = '{}.feat'.format
        cf = {
            'bold': os.path.join(folders['prepdir'], fmt(sub_id),
                                 'filtered_func_data.nii.gz'),
            'masked': os.path.join(folders['resdir'], sub_id, 'filtered_func_masked.nii.gz'),
            'mask': os.path.join(folders['prepdir'], fmt(sub_id), 'mask.nii.gz'),
            'smoothed': os.path.join(folders['resdir'], sub_id, 'filtered_func_smoothed.nii.gz'),
            'confoundsfile': os.path.join(folders['prepdir'], fmt(sub_id),
                                          'mc', 'prefiltered_func_data_mcf.par'),
            'warpfile': os.path.join(folders['prepdir'], fmt(sub_id), 'reg',
                                     'example_func2standard_warp.nii.gz'),
            'standard': os.path.join(folders['prepdir'], fmt(sub_id), 'reg',
                                     'standard.nii.gz'),
            'standard_mask': os.path.join(folders['prepdir'], fmt(sub_id), 'reg',
                                          'standard_mask.nii.gz')
        }
    return cf
