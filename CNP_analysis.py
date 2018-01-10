#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nipype.interfaces.fsl import model, FEATModel, FEAT, Level1Design, Smooth, maths
from nipype.interfaces.utility.base import IdentityInterface
from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.io import SelectFiles, DataSink
from nipype.algorithms.modelgen import SpecifyModel
from utils import utils, get_config
from nipype.interfaces import afni
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
parser.add_argument('-prep_pipeline','--prep_pipeline',dest='prep_pipeline',
                    help='preprocessing pipeline (fmriprep or feat)', required=True)
args = parser.parse_args()

# INPUT FILES AND FOLDERS

BIDSDIR = os.environ.get('BIDSDIR')
SUBJECT = args.subject

cf = get_config.get_folders(args.prep_pipeline)

for TASK in ['stopsignal']:
    cf_files = get_config.get_files(args.prep_pipeline,SUBJECT,TASK)

    bidssub = os.listdir(os.path.join(BIDSDIR, SUBJECT, 'func'))
    taskfiles = [x for x in bidssub if TASK in x]
    if len(taskfiles) == 0:  # if no files for this task are present: skip task
        continue

    if utils.check_exceptions(SUBJECT, TASK) == False:
        continue

    # CREATE OUTPUT DIRECTORIES
    if not os.path.exists(cf['resdir']):
        os.mkdir(cf['resdir'])

    subdir = os.path.join(cf['resdir'], SUBJECT)
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    if os.path.exists(os.path.join(subdir, '%s.feat' % TASK)):
        continue

    taskdir = os.path.join(cf['resdir'], SUBJECT, TASK)
    if not os.path.exists(taskdir):
        os.mkdir(taskdir)

    eventsdir = os.path.join(taskdir, 'events')
    if not os.path.exists(eventsdir):
        os.mkdir(eventsdir)

    os.chdir(taskdir)

    # GENERATE TASK REGRESSORS, CONTRASTS + CONFOUNDERS
    if args.prep_pipeline.startswith('fmriprep'):
        confounds_infile = cf_files['confoundsfile']
        confounds_in = pd.read_csv(confounds_infile, sep="\t")
        confounds_in = confounds_in[['stdDVARS', 'non-stdDVARS', 'vx-wisestdDVARS',
                                     'FramewiseDisplacement', 'X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']]
        confoundsfile = utils.create_confounds(confounds_in, eventsdir)
    else:
        confoundsfile = cf_files['confoundsfile']

    eventsfile = os.path.join(BIDSDIR, SUBJECT, 'func',
                              SUBJECT + "_task-" + TASK + '_events.tsv')
    regressors = utils.create_ev_task(eventsfile, eventsdir, TASK)
    EVfiles = regressors['EVfiles']
    orthogonality = regressors['orthogonal']

    contrasts = utils.create_contrasts(TASK)

    # START PIPELINE

    masker = Node(maths.ApplyMask(
        in_file=cf_files['bold'],
        out_file=cf_files['masked'],
        mask_file=cf_files['mask']
    ), name='masker')

    bandpass = Node(afni.Bandpass(
        highpass = 0.01,
        lowpass = 1,
        outputtype = "NIFTI_GZ"
        ), name = 'afni_bandpass')

    bim = Node(afni.BlurInMask(
        mask=cf_files['mask'],
        out_file=cf_files['smoothed'],
        fwhm=8.0
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
    CNPflow.connect([(masker, bandpass, [('out_file', 'in_file')]),
                     (bandpass, bim, [('out_file', 'in_file')]),
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
