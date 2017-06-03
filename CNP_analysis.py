#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nipype.interfaces.fsl import model, FEATModel, FEAT, Level1Design, Smooth, maths
from nipype.interfaces.utility.base import IdentityInterface
from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.io import SelectFiles, DataSink
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import afni
from utils import utils
import nibabel as nib
import pandas as pd
import numpy as np
import argparse
import shutil
import sys
import os

parser = argparse.ArgumentParser(
    description='Perform analysis on CNP task data')
parser.add_argument('-subject', '--subject', dest='subject',
                    help='subject label', required=True)
args = parser.parse_args()

# INPUT FILES AND FOLDERS

BIDSDIR = os.environ.get('BIDSDIR')
PREPDIR = os.environ.get("PREPDIR")
OUTDIR = os.environ.get("RESUDIR")
SUBJECT = args.subject

for TASK in ['stopsignal', 'taskswitch', 'scap', 'bart', 'pamret']:
    bidssub = os.listdir(os.path.join(BIDSDIR, SUBJECT, 'func'))
    taskfiles = [x for x in bidssub if TASK in x]
    if len(taskfiles) == 0:  # if no files for this task are present: skip task
        continue

    if utils.check_exceptions(SUBJECT, TASK) == False:
        continue

    # CREATE OUTPUT DIRECTORIES

    subdir = os.path.join(OUTDIR, SUBJECT)
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    if os.path.exists(os.path.join(subdir, '%s.feat' % task)):
        continue

    taskdir = os.path.join(OUTDIR, SUBJECT, TASK)
    if not os.path.exists(taskdir):
        os.mkdir(taskdir)

    eventsdir = os.path.join(taskdir, 'events')
    if not os.path.exists(eventsdir):
        os.mkdir(eventsdir)

    os.chdir(taskdir)

    # GENERATE TASK REGRESSORS, CONTRASTS + CONFOUNDERS

    confounds_infile = os.path.join(
        PREPDIR, SUBJECT, 'func', SUBJECT + "_task-" + TASK + '_bold_confounds.tsv')
    confounds_in = pd.read_csv(confounds_infile, sep="\t")
    confounds_in = confounds_in[['stdDVARS', 'non-stdDVARS', 'vx-wisestdDVARS',
                                 'FramewiseDisplacement', 'X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']]
    confoundsfile = utils.create_confounds(confounds_in, eventsdir)

    eventsfile = os.path.join(BIDSDIR, SUBJECT, 'func',
                              SUBJECT + "_task-" + TASK + '_events.tsv')
    regressors = utils.create_ev_task(eventsfile, eventsdir, TASK)
    EVfiles = regressors['EVfiles']
    orthogonality = regressors['orthogonal']

    contrasts = utils.create_contrasts(TASK)

    # START PIPELINE

    masker = Node(maths.ApplyMask(
        in_file=os.path.join(PREPDIR, SUBJECT, "func", SUBJECT + "_task-" +
                             TASK + "_bold_space-MNI152NLin2009cAsym_preproc.nii.gz"),
        out_file=os.path.join(taskdir, SUBJECT + "_task-" + TASK +
                              "_bold_space-MNI152NLin2009cAsym_preproc_masked.nii.gz"),
        mask_file=os.path.join(PREPDIR, SUBJECT, "func", SUBJECT + "_task-" +
                               TASK + "_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz")
    ), name='masker')

    bim = Node(afni.BlurInMask(
        mask=os.path.join(PREPDIR, SUBJECT, "func", SUBJECT + "_task-" +
                          TASK + "_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz"),
        out_file=os.path.join(taskdir, SUBJECT + "_task-" + TASK +
                              "_bold_space-MNI152NLin2009cAsym_preproc_smooth.nii.gz"),
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
    CNPflow.connect([(masker, bim, [('out_file', 'in_file')]),
                     (bim, l1, [('out_file', 'functional_runs')]),
                     (l1, l1model, [('session_info', 'session_info')]),
                     (l1model, l1featmodel, [
                      ('fsf_files', 'fsf_file'), ('ev_files', 'ev_files')]),
                     (l1model, l1estimate, [('fsf_files', 'fsf_file')])
                     ])

    CNPflow.write_graph(graph2use='colored')
    CNPflow.run('MultiProc', plugin_args={'n_procs': 4})

    featdir = os.path.join(taskdir, "cnp", 'l1estimate', 'run0.feat')
    utils.purge_feat(featdir)

    shutil.move(featdir, os.path.join(subdir, '%s.feat' % TASK))
    shutil.rmtree(taskdir)
