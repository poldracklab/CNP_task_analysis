#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from nilearn.image import resample_to_img
import nibabel as nib
import numpy as np
import sys
import os

# Atlases and effect sizes in regions

def create_atlas():
    # 1: left STN
    # 2: right STN
    STN_05 = os.path.join(os.environ.get("FSLDIR"),'data/atlases/STN/STN-maxprob-thr0-0.5mm.nii.gz')
    # 4: Inferior Frontal Gyrus, pars triangularis
    # 25: Juxtapositional Lobule Cortex (formerly Supplementary Motor Cortex)
    # 7: Precentral gyrus (motor)
    HO = os.path.join(os.environ.get("FSLDIR"),'data/atlases/HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm.nii.gz')
    STN = resample_to_img(STN_05, HO, interpolation='nearest')
    STN_dat = STN.get_data()
    HO_dat = nib.load(HO).get_data()

    assert(len(np.where(np.logical_and(HO_dat!=0,STN_dat!=0))[0])==0)

    newat = np.zeros(STN.shape[:3])
    newat[np.where(HO_dat==7)] = 4
    newat[np.where(HO_dat==5)] = 3
    newat[np.where(HO_dat==26)] = 2
    newat[np.where(STN_dat>0)] = 1
    atlas = nib.Nifti1Image(newat,affine=STN.affine,header=STN.header)
    labels = {
        1:"STN",
        2:"preSMA",
        3:"IFG",
        4:"PCG"
    }
    return atlas,labels
