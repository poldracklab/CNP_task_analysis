#!/usr/bin/env python
# coding: utf-8
from __future__ import division, absolute_import

import os
import sys
import glob
import numpy as np
import json
import nibabel as nb
import pandas as pd
from scipy.stats import pearsonr
from nilearn.image import resample_to_img
from nipype.algorithms.metrics import FuzzyOverlap

GROUP_MASK = ('/oak/stanford/groups/russpold/data/templates/'
              'mni_icbm152_nlin_asym_09c/2mm_brainmask.nii.gz')

# Overlap measures
def dice(im1, im2, in_mask=None):
    overlap = FuzzyOverlap()
    overlap.inputs.in_ref = [im1]
    overlap.inputs.in_tst = [im2]

    if in_mask is not None:
        overlap.inputs.in_mask = in_mask
    res = overlap.run()
    return res.outputs.dice


def cohen(tstat, atlas, labels, samplesize):
    res = {}
    for k, v in labels.items():
        indxs = np.where(atlas == k)
        T = tstat[indxs]
        CD = np.mean(T) / np.sqrt(samplesize)
        res[v] = CD
    return res


def create_atlas():
    # 1: left STN
    # 2: right STN
    STN_05 = os.path.join(os.getenv("FSLDIR"),
                          'data/atlases/STN/STN-maxprob-thr0-0.5mm.nii.gz')
    stn_05_2mm = resample_to_img(STN_05, GROUP_MASK,
                                 interpolation='nearest').get_data()
    # 4: Inferior Frontal Gyrus, pars triangularis
    # 25: Juxtapositional Lobule Cortex (formerly Supplementary Motor Cortex)
    # 7: Precentral gyrus (motor)
    HO = os.path.join(os.getenv("FSLDIR"),
                      'data/atlases/HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm.nii.gz')
    ho_2mm = resample_to_img(
        HO, GROUP_MASK, interpolation='nearest').get_data().astype(np.uint8)

    atlas_data = np.zeros_like(ho_2mm, dtype=np.uint8)
    atlas_data[stn_05_2mm > 1] = 1
    atlas_data[ho_2mm == 26] = 2
    atlas_data[ho_2mm == 5] = 3
    atlas_data[ho_2mm == 7] = 4
    labels = {
        1: "STN",
        2: "preSMA",
        3: "IFG",
        4: "PCG"
    }
    return atlas_data, labels


# COLLECT
def main():
    atlas_data, labels = create_atlas()
    results = pd.DataFrame()

    # Pattern: l2-jd/fslfeat_stopsignal_N120_R100_S0
    basedir = os.path.join(os.environ.get("PREPBASEDIR"), "fmriprep_vs_feat_2.0-jd", 'l2-jd')
    l1results = [os.path.basename(f)[:-1] 
                 for f in sorted(glob.glob(os.path.join(basedir, '*_S0')))]
    allT = {
        'fmriprep': {},
        'fslfeat': {}
    }
    for i, res in enumerate(l1results):
        print('Processing experiment: %s' % res)
        s1 = os.path.join(basedir, '%s0' % res)
        s2 = os.path.join(basedir, '%s1' % res)

        pipeline, task, samplesize, exp, _ = res.split('_')
        samplesize = int(samplesize[1:])
        exp = int(exp[1:])

        tvals = [
            nb.load(os.path.join(s1, 'tstat1.nii.gz')).get_data(),
            nb.load(os.path.join(s2, 'tstat1.nii.gz')).get_data()]
        # compute mask to have exactly same values
        tmpmask = np.where(np.logical_and(tvals[0] != 0, tvals[1] != 0))

        tvs = [x[tmpmask].tolist() for x in tvals]
        tvs = [x for sublist in tvs for x in sublist]
        sel = np.random.choice(tvs, 100).tolist()

        if ('%d' % samplesize) not in allT[pipeline]:
            allT[pipeline]['%d' % samplesize] = []

        allT[pipeline]['%d' % samplesize] += sel

        csvrow = {
            'pipeline': pipeline,
            'repetition': exp,
            'N': samplesize,
        }
        csvrow.update(cohen(tvals[0], atlas_data, labels, samplesize))

        # compute correlation
        csvrow["correlation"] = pearsonr(tvals[0][tmpmask], tvals[1][tmpmask])[0]

        pval_names = [os.path.join(s, 'zstat1_pval.nii.gz')
                      for s in [s1, s2]]
        pvals = [nb.load(f).get_data() for f in pval_names]

        # compute fuzzy dice
        csvrow["fdice"] = dice(*pval_names)
        csvrow["fdice_masked"] = dice(*pval_names, in_mask=GROUP_MASK)
        
        binmap = [os.path.join(s, 'zstat1_thresh.nii.gz') for s in [s1, s2]]

        # compute dice
        csvrow["dice"] = dice(*binmap)
        csvrow["dice_masked"] = dice(*binmap, in_mask=GROUP_MASK)
        # Add to Dataframe
        results = results.append(csvrow, ignore_index=True)
        print('Added row: %s' % csvrow)

    with open(os.path.join(basedir, "tvals.json"), 'w') as outfile:
        json.dump(allT, outfile)
    results.to_csv(os.path.join(basedir, "group.csv"))
    print('Results file written out to %s.' % os.path.join(basedir, "group.csv"))


if __name__ == '__main__':
    main()
