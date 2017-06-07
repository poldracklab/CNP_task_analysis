from nilearn import plotting
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import os
import json
from matplotlib.colors import LinearSegmentedColormap

groupdir = os.environ.get("GROUPDIR")
homedir = os.environ.get("HOMEDIR")
acmdir = os.environ.get("ACMDIR")
figdir = os.environ.get("FIGDIR")

contrastfile = os.path.join(homedir,"utils/contrasts.json")
with open(contrastfile) as fl:
    contrasts = json.load(fl)

papershow = {'bart':[1,3,5,9,13],
             'scap':[1,3,19,21],
             'stopsignal':[1,3,11,15],
             'taskswitch':[1,3,37,39],
             'pamret':[1,3,27,31]
             }

for task in ['stopsignal', 'taskswitch', 'scap', 'bart', 'pamret']:
    for contrast in papershow[task]:

        # task = 'pamret'
        # contrast = 1
        contrastname = contrasts[task][contrast-1]

        MNItemplate = os.path.join(os.environ.get('FSLDIR'),'data/standard/MNI152_T1_0.5mm.nii.gz')
        flame_z = os.path.join(groupdir,task,'cope%i'%contrast,'OLS/zstat1.nii.gz')
        acm = os.path.join(acmdir,task,"zstat%i_ACM_diff.nii.gz"%contrast)
        acm_neg = os.path.join(acmdir,task,"zstat%i_ACM_neg.nii.gz"%contrast)

        title = "%s - %s"%(task,contrastname)
        outfile = os.path.join(figdir,"%s_%i_z.pdf"%(task,contrast))
        plotting.plot_glass_brain(flame_z,colorbar=True,cmap="RdYlBu_r",title=title,plot_abs=False,vmin=-15,vmax=15,output_file=outfile)
        outfile = os.path.join(figdir,"%s_%i_acm.pdf"%(task,contrast))
        plotting.plot_glass_brain(acm,colorbar=True,cmap='PRGn',title=title,plot_abs=False,vmin=-1,vmax=1,output_file=outfile)


        #plotting.plot_stat_map(flame_z,bg_img=MNItemplate,colorbar=True,cmap="RdYlBu_r",title=title,threshold=2.3,cut_coords=[40,0,0])
