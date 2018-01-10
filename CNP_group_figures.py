from nilearn import plotting
import nibabel as nib
import numpy as np
import json
import os

parser = argparse.ArgumentParser(description='Perform analysis on CNP task data')
parser.add_argument('-prep_pipeline','--prep_pipeline',dest='prep_pipeline',help='preprocessing pipeline',required=True)

args = parser.parse_args()

cf = get_config.get_folders(args.prep_pipeline)
groupdir = cf['groupdir']
acmdir = cf['acmdir']
figdir = cf['figdir']

homedir = os.environ.get("HOMEDIR")

contrastfile = os.path.join(homedir,"utils/contrasts.json")
with open(contrastfile) as fl:
    contrasts = json.load(fl)

papershow = {'bart':[1,3,5,9,13],
             'scap':[1,3,19,21],
             'stopsignal':[1,3,11,15],
             'taskswitch':[1,3,37,39],
             'pamret':[1,3,27,31]
             }

samplesizes = {'bart':259,
             'scap':244,
             'stopsignal':255,
             'taskswitch':254,
             'pamret':197
             }

for task in ['stopsignal', 'taskswitch', 'scap', 'bart', 'pamret']:
    for contrast in papershow[task]:
        print("task: %s - contrast: %s"%(task,str(contrast)))

        # task = 'pamret'
        # contrast = 1
        contrastname = contrasts[task][contrast-1]

        MNItemplate = os.path.join(os.environ.get('FSLDIR'),'data/standard/MNI152_T1_0.5mm.nii.gz')
        rand_t = os.path.join(groupdir,task,'cope%i'%contrast,'randomise/randomise_tstat1.nii.gz')
        acm = os.path.join(acmdir,task,"zstat%i_ACM_diff.nii.gz"%contrast)
        acm_neg = os.path.join(acmdir,task,"zstat%i_ACM_neg.nii.gz"%contrast)

        tval = nib.load(rand_t).get_data()
        ss = samplesizes[task]
        cohen = tval/np.sqrt(ss)
        CD = nib.Nifti1Image(cohen,affine=nib.load(rand_t).get_affine(),header=nib.load(rand_t).get_header())

        title = "%s"%(contrastname)
        outfile = os.path.join(figdir,"%s_%s_z.pdf"%(task,contrastname))
        plotting.plot_glass_brain(rand_t,colorbar=True,cmap="RdYlBu_r",title=title,plot_abs=False,vmin=-10,vmax=10,output_file=outfile)
        outfile = os.path.join(figdir,"%s_%s_acm.pdf"%(task,contrastname))
        plotting.plot_glass_brain(acm,colorbar=True,cmap='PRGn',title=title,plot_abs=False,vmin=-1,vmax=1,output_file=outfile)
        outfile = os.path.join(figdir,"%s_%s_cd.pdf"%(task,contrastname))
        plotting.plot_glass_brain(CD,colorbar=True,cmap='BrBG',title=title,plot_abs=False,vmin=-1,vmax=1,output_file=outfile)
        outfile = os.path.join(figdir,"slices_%s_%s.pdf"%(task,contrastname))
        plotting.plot_stat_map(rand_t,threshold=3.1,display_mode='z',cut_coords=8,dim=-0.2,output_file=outfile)
