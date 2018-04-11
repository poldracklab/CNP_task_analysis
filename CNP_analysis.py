#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
First-level analysis of the CNP dataset
"""

import os
import shutil
from warnings import warn
from nipype.interfaces.fsl import FEATModel, FEAT, Level1Design, maths
from nipype.pipeline.engine import Workflow, Node
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import afni
from nipype.interfaces import utility as niu

from utils.utils import create_contrasts, create_ev_task


GROUP_MASK = ('/oak/stanford/groups/russpold/data/'
              'templates/mni_icbm152_nlin_asym_09c/2mm_brainmask.nii.gz')


def get_parser():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', action='store',
                        help='pipeline name')
    parser.add_argument('subject', action='store', help='subject label')
    parser.add_argument('-t', '--tasks', nargs='+', type=str, action='store',
                        help='list of tasks to be processed')
    parser.add_argument('-B', '--bids-dir', action='store', default=os.getenv('BIDSDIR'))
    parser.add_argument('-D', '--deriv-dir', action='store',
                        default=os.environ.get('PREPBASEDIR'),
                        help='path to a BIDS-Derivatives folder with '
                             'preprocessed data')
    parser.add_argument('-R', '--results-dir', action='store',
                        default=os.environ.get('PREPBASEDIR'),
                        help='path to a BIDS-Derivatives folder '
                             'where results will be stored')
    parser.add_argument('-w', '--work-dir', action='store',
                        default=os.path.join(os.getcwd(), 'work'),
                        help='work directory')
    parser.add_argument('--variant', action='store',
                        help='preprocessing workflow name')
    return parser


def _confounds2movpar(in_confounds):
    from os.path import abspath
    import numpy as np
    import pandas as pd
    dataframe = pd.read_csv(
        in_confounds,
        sep='\t',
        usecols=['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']).fillna(value=0)

    out_name = abspath('motion.par')
    np.savetxt(out_name, dataframe.values, '%5.3f')
    return out_name


def main():
    args = get_parser().parse_args()

    # INPUT FILES AND FOLDERS
    bids_dir = args.bids_dir
    if bids_dir is None:
        raise RuntimeError(
            'No BIDS root directory was specified. Please provide it with '
            'the --bids-dir argument or using the BIDSDIR env variable.')

    deriv_dir = args.deriv_dir
    if deriv_dir is None:
        raise RuntimeError(
            'No BIDS-Derivatives folder with pre-processed inputs was '
            'specified. Please provide it with the --deriv-dir argument '
            'or using the PREPBASEDIR environment variable.')

    if not args.tasks:
        raise RuntimeError(
            'No tasks were provided. Please indicate a task with the '
            '--tasks argument.')

    variant = args.variant
    if variant is None:
        variant = 'fmriprep' if 'fmriprep' in os.path.basename(deriv_dir) \
            else 'fslfeat'

    res_dir = os.path.abspath(os.path.join(args.results_dir, variant))
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    work_dir = args.work_dir
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    # Set subject name
    subject = args.subject if args.subject.startswith('sub-') \
        else 'sub-%s' % args.subject

    fmt = '{subject}_task-{task_id}_{suffix}'.format

    print('Building workflow for tasks: %s.' % ', '.join(args.tasks))
    for task_id in args.tasks:
        prep_file = os.path.join(
            deriv_dir, subject, 'func', fmt(
                subject=subject, task_id=task_id,
                suffix='bold_space-MNI152NLin2009cAsym_preproc.nii.gz')
        )

        if not os.path.isfile(prep_file):
            warn('Preprocessed file not found: %s' % prep_file)
            continue

        # START PIPELINE
        # inputmask = Node(IdentityInterface(fields=['mask_file']), name='inputmask')
        conf2movpar = Node(niu.Function(function=_confounds2movpar),
                           name='conf2movpar')
        conf2movpar.inputs.in_confounds = os.path.join(
            deriv_dir, subject, 'func', fmt(
                subject=subject, task_id=task_id,
                suffix='bold_confounds.tsv')
        )

        regressors = Node(niu.Function(
            function=create_ev_task,
            output_names=['ev_files', 'ortho']), name='regressors')
        regressors.inputs.eventsfile = os.path.join(
            bids_dir, subject, 'func', fmt(
                subject=subject, task_id=task_id,
                suffix='events.tsv'))
        regressors.inputs.task_id = task_id

        contrasts = Node(niu.Function(function=create_contrasts), name='contrasts')
        contrasts.inputs.task = task_id

        masker = Node(maths.ApplyMask(
            in_file=prep_file, mask_file=GROUP_MASK), name='masker')

        bim = Node(afni.BlurInMask(
            mask=GROUP_MASK, outputtype='NIFTI_GZ', fwhm=5.0), name='bim')

        l1 = Node(SpecifyModel(
            input_units='secs',
            time_repetition=2,
            high_pass_filter_cutoff=100
        ), name='l1')

        l1model = Node(Level1Design(
            interscan_interval=2,
            bases={'dgamma': {'derivs': True}},
            model_serial_correlations=True,
        ), name='l1design')

        l1featmodel = Node(FEATModel(), name='l1model')

        l1estimate = Node(FEAT(), name='l1estimate')

        wfname = '_'.join(('l1', variant, subject[4:]))
        CNPflow = Workflow(name=wfname)
        CNPflow.base_dir = work_dir
        CNPflow.connect([
            (masker, bim, [('out_file', 'in_file')]),
            (bim, l1, [('out_file', 'functional_runs')]),
            (conf2movpar, l1, [('out', 'realignment_parameters')]),
            (regressors, l1, [('ev_files', 'event_files')]),
            (regressors, l1model, [('ortho', 'orthogonalization')]),
            (contrasts, l1model, [('out', 'contrasts')]),
            (l1, l1model, [('session_info', 'session_info')]),
            (l1model, l1featmodel, [
                ('fsf_files', 'fsf_file'),
                ('ev_files', 'ev_files')]),
            (l1model, l1estimate, [('fsf_files', 'fsf_file')])
        ])

        CNPflow.write_graph(graph2use='colored')
        CNPflow.run('MultiProc')

        sub_dir = os.path.join(res_dir, '_'.join(
            (subject, 'task-%s' % task_id)))

        if os.path.exists(sub_dir):
            shutil.rmtree(sub_dir)
        featdir = os.path.join(work_dir, wfname, 'l1estimate', 'run0.feat')
        shutil.copytree(featdir, os.path.join(sub_dir))
        return 0


if __name__ == '__main__':
    import sys
    code = main()
    sys.exit(code)
