#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
First-level analysis of the CNP dataset
"""

import os
import shutil
import argparse
import pandas as pd
from warnings import warn
from nipype.interfaces.fsl import FEATModel, FEAT, Level1Design, maths
from nipype.pipeline.engine import Workflow, Node
from nipype.algorithms.modelgen import SpecifyModel
from utils import utils, get_config
from nipype.interfaces import afni


# def _nilearnmask(in_file, mask_file):
#     import os
#     import numpy as np
#     import nibabel as nb
#     from nipype.utils.filemanip import fname_presuffix
#     from nilearn.image import resample_to_img
#     out_file = fname_presuffix(in_file, '_brain', newpath=os.getcwd())
#     out_mask = fname_presuffix(in_file, '_brainmask', newpath=os.getcwd())
#     newmask = resample_to_img(mask_file, in_file,
#                               interpolation='nearest')
#     newmask.to_filename(out_mask)
#     nii = nb.load(in_file)
#     data = nii.get_data() * newmask.get_data()[..., np.newaxis]
#     nii = nii.__class__(data, nii.affine, nii.header).to_filename(out_file)
#     return out_file, out_mask

def get_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('subject', action='store', help='subject label')
    parser.add_argument('pipeline', dest='prep_pipeline', action='store',
                        help='preprocessing pipeline (fmriprep or feat)')
    parser.add_argument('--bids-dir', action='store', default=os.getenv('BIDSDIR'))
    return parser


args = get_parser().parse_args()

# INPUT FILES AND FOLDERS
BIDSDIR = args.bids_dir
if BIDSDIR is None:
    raise RuntimeError(
        'No BIDS root directory was specified. Please provide it with '
        'the --bids-dir argument or using the BIDSDIR env variable.')

SUBJECT = args.subject

cf = get_config.get_folders(args.prep_pipeline)

for task_id in ['stopsignal']:
    cf_files = get_config.get_files(args.prep_pipeline, SUBJECT, task_id)

    bidssub = os.listdir(os.path.join(BIDSDIR, SUBJECT, 'func'))
    taskfiles = [x for x in bidssub if task_id in x]
    if len(taskfiles) == 0:  # if no files for this task are present: skip task
        warn('No task "%s" found for subject "%s". Skipping.' % (task_id, SUBJECT))
        continue

    if not utils.check_exceptions(SUBJECT, task_id):
        warn('Skipping subject "%s", task "%s".' % (SUBJECT, task_id))
        continue

    # CREATE OUTPUT DIRECTORIES
    if not os.path.exists(cf['resdir']):
        os.mkdir(cf['resdir'])

    subdir = os.path.join(cf['resdir'], SUBJECT)
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    if os.path.exists(os.path.join(subdir, '%s.feat' % task_id)):
        warn('Folder "%s" exists, skipping.' %
             os.path.join(subdir, '%s.feat' % task_id))
        continue

    taskdir = os.path.join(cf['resdir'], SUBJECT, task_id)
    if not os.path.exists(taskdir):
        os.mkdir(taskdir)

    eventsdir = os.path.join(taskdir, 'events')
    if not os.path.exists(eventsdir):
        os.mkdir(eventsdir)

    os.chdir(taskdir)

    # GENERATE task_id REGRESSORS, CONTRASTS + CONFOUNDERS
    confounds_infile = cf_files['confoundsfile']
    confounds_in = pd.read_csv(confounds_infile, sep="\t")
    confounds_in = confounds_in[['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']]
    confoundsfile = utils.create_confounds(confounds_in, eventsdir)

    eventsfile = os.path.join(BIDSDIR, SUBJECT, 'func',
                              '%s_task-%s_events.tsv' % (SUBJECT, task_id))

    regressors = utils.create_ev_task(eventsfile, eventsdir, task_id)
    EVfiles = regressors['EVfiles']
    orthogonality = regressors['orthogonal']

    contrasts = utils.create_contrasts(task_id)

    # START PIPELINE
    # inputmask = Node(IdentityInterface(fields=['mask_file']), name='inputmask')
    masker = Node(maths.ApplyMask(
        in_file=cf_files['bold'],
        out_file=cf_files['masked'],
        mask_file=cf_files['standard_mask']
    ), name='masker')

    bim = Node(afni.BlurInMask(
        out_file=cf_files['smoothed'],
        mask=cf_files['standard_mask'],
        fwhm=5.0
    ), name='bim')

    l1 = Node(SpecifyModel(
        event_files=EVfiles,
        realignment_parameters=confoundsfile,
        input_units='secs',
        time_repetition=2,
        high_pass_filter_cutoff=100
    ), name='l1')

    l1model = Node(Level1Design(
        interscan_interval=2,
        bases={'dgamma': {'derivs': True}},
        model_serial_correlations=True,
        orthogonalization=orthogonality,
        contrasts=contrasts
    ), name='l1design')

    l1featmodel = Node(FEATModel(), name='l1model')

    l1estimate = Node(FEAT(), name='l1estimate')

    CNPflow = Workflow(name='cnp')
    CNPflow.base_dir = taskdir
    CNPflow.connect([
        (masker, bim, [('out_file', 'in_file')]),
        (bim, l1, [('out_file', 'functional_runs')]),
        (l1, l1model, [('session_info', 'session_info')]),
        (l1model, l1featmodel, [
            ('fsf_files', 'fsf_file'),
            ('ev_files', 'ev_files')]),
        (l1model, l1estimate, [('fsf_files', 'fsf_file')])
    ])

    CNPflow.write_graph(graph2use='colored')
    CNPflow.run('MultiProc', plugin_args={'n_procs': 4})

    featdir = os.path.join(taskdir, "cnp", 'l1estimate', 'run0.feat')
    utils.purge_feat(featdir)

    shutil.move(featdir, os.path.join(subdir, '%s.feat' % task_id))
    shutil.rmtree(taskdir)
