import os
import sys
import inspect
import numpy as np
from nipype.interfaces import fsl
from nipype.interfaces import io as nio
from nipype.interfaces.utility import Function
from nipype.pipeline.engine import Workflow, Node

GROUP_MASK = ('/oak/stanford/groups/russpold/data/'
              'templates/mni_icbm152_nlin_asym_09c/2mm_brainmask.nii.gz')


def get_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
    parser.add_argument('name', action='store', help='workflow name')
    parser.add_argument('-t', '--task', action='store', help='task name',
                        required=True)
    parser.add_argument('-c', '--contrast', action='store', type=int,
                        help='contrast number', required=True)
    parser.add_argument('-e', '--experiment', action='store', type=int,
                        help='experiment number', required=True)

    parser.add_argument('-B', '--bids-dir', action='store',
                        default=os.environ.get('BIDSDIR'),
                        help='path to the original BIDS root folder')
    parser.add_argument('-P', '--deriv-dir', action='store',
                        default=os.environ.get('PREPBASEDIR'),
                        help='path to a BIDS-Derivatives folder with '
                             'preprocessed data')
    parser.add_argument('-w', '--work-dir', action='store',
                        default=os.path.join(os.getcwd(), 'work'),
                        help='work directory')
    return parser


def thresholding(samplesize, zstat1, cope1, res4d, mask):
    ##################
    #  THRESHOLDING ##
    ##################
    import os

    # FDR
    os.popen('fslmaths %s -ztop zstat1_pval' % zstat1).read()
    logpcmd = 'fdr -i zstat1_pval -m %s -q 0.05' % mask

    pstat = os.path.abspath('zstat1_pval.nii.gz')
    thres = 1 - float(os.popen(logpcmd).read().split('\n')[1])
    threscmd = ('fslmaths zstat1_pval -mul -1 -add 1 -thr %f '
                '-mas %s zstat1_thresh_vox_fdr_pstat1') % (
        thres, mask)
    os.popen(threscmd).read()
    fdr_thres = os.path.abspath('zstat1_thresh_vox_fdr_pstat1.nii.gz')

    # FWE
    smoothcmd = 'smoothest -r %s -d %i -m %s' % (
        res4d, samplesize - 1, mask)
    smooth = os.popen(smoothcmd).read().split("\n")
    smoothn = [x.split(' ')[1] for x in smooth[:-1]]
    reselcount = float(smoothn[1]) / float(smoothn[2])
    fwethrescmd = 'ptoz 0.05 -g %f' % reselcount
    fwethres = os.popen(fwethrescmd).read().split("\n")[0]
    fwecmd = 'fslmaths %s -thr %s zstat1_thresh' % (
        zstat1, fwethres)
    os.popen(fwecmd).read()
    fwe_thres = os.path.abspath('zstat1_thresh.nii.gz')

    # cluster extent
    clustercmd = (
        'cluster -i %s -c %s -t 3.2 -p 0.05 -d %s --volume=%s'
        ' --othresh=thresh_cluster_fwe_zstat1 --connectivity=26 --mm') % (
        zstat1, cope1, smoothn[0], smoothn[1])
    clusterout = os.popen(clustercmd).read()
    with open('thres_cluster_fwe_table.txt', 'w+') as f1:
        f1.write(clusterout)
    return pstat, fdr_thres, fwe_thres


def main():
    args = get_parser().parse_args()

    if args.bids_dir is None:
        raise RuntimeError('--bids-dir not provided, and $BIDSDIR not set')

    # Setup output dir
    deriv_dir = args.deriv_dir
    if deriv_dir is None:
        deriv_dir = os.path.join(args.bids_dir, 'derivatives')
    base_dir = os.path.join(deriv_dir, args.name)
    groupdir = os.path.join(base_dir, 'l2-jd')

    if not os.path.exists(groupdir):
        os.makedirs(groupdir)

    ##############################
    # TAKE SAMPLE FOR EXPERIMENT #
    ##############################

    # collect subjects
    whitelist = os.path.join(
        os.path.dirname(inspect.getfile(inspect.currentframe())),
        'utils', 'CNP-stopsignal-whitelist.txt')

    with open(whitelist) as f:
        subjects = [s.strip('\n') for s in f.read().splitlines()]

    start = 10
    experiment = args.experiment
    for samplesize in np.arange(start, 125, 5).tolist():
        np.random.seed(experiment * samplesize)

        sample = np.random.choice(len(subjects), samplesize * 2, replace=False)
        sample = [sorted(np.array(subjects)[sample[:samplesize]].tolist()),
                  sorted(np.array(subjects)[sample[samplesize:]].tolist())]

        print("##################################################")
        print("# Started samplesize %3d - Sampled subjects:    #" % samplesize)
        print("##################################################")
        print(", ".join(sample[0]))
        print(", ".join(sample[1]))
        print("##################################################")

        task = args.task
        contrast = args.contrast

        # loop over pipelines
        for pipe in ['fmriprep', 'fslfeat']:
            for gid in range(2):
                print("Starting Sample %i" % gid)
                expname = ('%s_%s_N%03d_R%03d_S%d' % (
                           pipe, task, samplesize, experiment, gid))
                destdir = os.path.join(groupdir, expname)
                if not os.path.exists(destdir):
                    os.makedirs(destdir)

                group_pattern = [
                    os.path.join(
                        base_dir, 'sub-%s' % s, 'func',
                        'sub-{}_task-{}_variant-{}_%s{:d}.nii.gz'.format(
                            s, task, pipe, contrast))
                    for s in sample[gid]
                ]

                copes = [gpatt % 'cope' for gpatt in group_pattern]
                varcopes = [gpatt % 'varcope' for gpatt in group_pattern]

                # define nodes
                copemerge = Node(fsl.Merge(
                    dimension='t',
                    in_files=copes),
                    name='copemerge')
                varcopemerge = Node(fsl.Merge(
                    dimension='t',
                    in_files=varcopes),
                    name='varcopemerge')
                level2model = Node(fsl.L2Model(
                    num_copes=len(copes)),
                    name='l2model')
                OLS = Node(fsl.FLAMEO(
                    run_mode='ols',
                    mask_file=GROUP_MASK), name='OLS')

                thres = Node(Function(
                    function=thresholding,
                    output_names=['pstat', 'fdr_thres', 'fwe_thres']),
                    name='thresholds')
                thres.inputs.mask = GROUP_MASK
                thres.inputs.samplesize = samplesize

                ds = Node(nio.DataSink(base_directory=groupdir),
                          name='_'.join(('ds', expname)))
                dsfmt = ('%s_%s_N%03d_R%03d_S%d.@{}' % (
                         pipe, task, samplesize, experiment, gid)).format

                # create workflow
                CNPgroup = Workflow(name='_'.join(('cnp', expname)))
                CNPgroup.base_dir = args.work_dir
                CNPgroup.connect([
                    (copemerge, OLS, [('merged_file', 'cope_file')]),
                    (varcopemerge, OLS, [('merged_file', 'var_cope_file')]),
                    (level2model, OLS, [('design_mat', 'design_file'),
                                        ('design_con', 't_con_file'),
                                        ('design_grp', 'cov_split_file')]),
                    (OLS, ds, [(('tstats', _first), dsfmt('tstat1')),
                               (('zstats', _first), dsfmt('zstat1'))]),
                    (OLS, thres, [
                        (('zstats', _first), 'zstat1'),
                        (('copes', _first), 'cope1'),
                        ('res4d', 'res4d')]),
                    (thres, ds, [
                        ('pstat', dsfmt('pstat')),
                        ('fdr_thres', dsfmt('fdr_thres')),
                        ('fwe_thres', dsfmt('fwe_thres'))]),
                ])

                CNPgroup.write_graph(graph2use='colored')
                CNPgroup.run('MultiProc', plugin_args={'n_procs': 4})

    return 0


def _first(inlist):
    if isinstance(inlist, (list, tuple)):
        return inlist[0]
    return inlist


if __name__ == '__main__':
    code = main()
    sys.exit(code)
