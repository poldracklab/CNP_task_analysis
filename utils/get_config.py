import sys
import os

# NOTE:
# This is assuming that the files are in $PREPBASEDIR/fmriprep and $PREPBASEDIR/feat

def get_folders(prep_pipeline):
    cf = {
        'prepdir':os.path.join(os.environ.get('PREPBASEDIR'),prep_pipeline),
        'resdir':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline,'derivatives','task'),
        'groupdir':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline,'derivatives','task_group'),
        'acmdir':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline,'derivatives','task_acm'),
        'figdir':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline,'derivatives','task_figures'),
        'condir':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline,'derivatives','conmaps')
    }
    return cf

def get_files(prep_pipeline,SUBJECT,TASK):
    if prep_pipeline == 'fmriprep':
        cf = {
            'bold':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline, SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_preproc.nii.gz"),
            'masked':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline, SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_preproc_masked.nii.gz"),
            'mask':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline, SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz"),
            'smoothed':os.path.join(os.environ.get("PREPBASEDIR"),prep_pipeline, SUBJECT, "func", SUBJECT + "_task-" + TASK + "_bold_space-MNI152NLin2009cAsym_smooth.nii.gz"),
            'confoundsfile': os.path.join(os.environ.get('PREPBASEDIR'),prep_pipeline, SUBJECT, 'func', SUBJECT + "_task-" + TASK + '_bold_confounds.tsv')
        }
    else:
        cf = {
            'bold':,
            'masked':,
            'mask':,
            'smoothed':,
            'confoundsfile':
        }
    return cf
