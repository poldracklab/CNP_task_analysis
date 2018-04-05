from __future__ import absolute_import
import os
from joblib import Parallel, delayed
import pandas as pd
import nibabel as nib
import numpy as np

from nipype.interfaces.fsl import SmoothEstimate
from nipype.interfaces.afni import FWHMx
from .utils import get_config


basedir = os.path.join(os.environ.get("PREPBASEDIR"), "fmriprep_vs_feat")

pipelines = ['fmriprep-1.0.3', 'fslfeat_5.0.9']


# single subject smoothness
def smoothafni(zstat, mask):
    est = FWHMx()
    est.inputs.in_file = zstat
    est.inputs.mask = mask
    est = est.run()
    fwhm = np.mean(est.outputs.fwhm)
    return fwhm


def smoothfsl(zstat, mask):
        est = SmoothEstimate()
        est.inputs.zstat_file = zstat
        est.inputs.mask_file = mask
        est = est.run()
        psize = nib.load(zstat).header.get_zooms()
        return (est.outputs.resels * np.product(psize)) ** (1 / 3.)


def get_smoothness(sub):
    res = []
    for pipeline in pipelines:
        cf = get_config.get_folders(pipeline)
        featdir = cf['resdir']
        cf_files = get_config.get_files(pipeline, sub, 'stopsignal')
        subfeatdir = os.path.join(featdir, sub, "stopsignal.feat")
        if not sub.startswith('sub-') or not os.path.exists(subfeatdir):
            continue
        zstat = os.path.join(subfeatdir, 'stats', 'zstat11.nii.gz')
        resid = os.path.join(subfeatdir, 'stats', 'res4d.nii.gz')
        mask = cf_files['standard_mask']
        newrow = {
            "subject": sub,
            'pipeline': pipeline,
            "FWHM_data": smoothfsl(cf_files['smoothed'], mask),
            "FWHM_zstat": smoothfsl(zstat, mask),
            "FWHM_resid": smoothfsl(resid, mask),
            "FWHM_unpr": smoothfsl(cf_files['masked'], mask)
        }
        res.append(newrow)
    return res


cf = get_config.get_folders('fslfeat_5.0.9')
featdir = cf['resdir']


# results = Parallel(n_jobs=16)(delayed(get_smoothness)(subject)
#                               for subject in os.listdir(featdir))
# resflat = [x for sublist in results for x in sublist]
# res = pd.DataFrame(resflat)
# res.to_csv(os.path.join(basedir,"smoothness_subjects.csv"))

# group analysis smoothness
def get_smoothness_group(samplesize, basedir):
    outlist = []
    for pipeline in ['fmriprep-1.0.3', 'fslfeat_5.0.9']:
        for experiment in range(1, 100):
            for sample in range(2):
                outdir = os.path.join(basedir, pipeline,
                                      'task_group/samplesize_%i' % samplesize,
                                      'experiment_%i' % experiment,
                                      "stopsignal/sample_%i/cope11/OLS/" % sample)
                zstat = os.path.join(outdir, 'zstat1.nii.gz')
                resid = os.path.join(outdir, 'res4d.nii.gz')
                mask = os.path.join(outdir, 'mask.nii.gz')
                sm = {
                    "FWHM_zstat": smoothfsl(zstat, mask),
                    "FWHM_resid": smoothfsl(resid, mask),
                    "experiment": experiment,
                    "samplesize": samplesize,
                    "pipeline": pipeline
                }
                outlist.append(sm)
    return outlist


groupresults = Parallel(n_jobs=16)(delayed(get_smoothness_group)(samplesize, basedir)
                                   for samplesize in np.arange(10, 101, 5).tolist())
groupresults = [x for x in groupresults if not x == 0]
resflat = [x for sublist in groupresults for x in sublist]
res = pd.DataFrame(resflat)
res.to_csv(os.path.join(basedir, "smoothness_group.csv"))
