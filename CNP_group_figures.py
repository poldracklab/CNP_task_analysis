from nilearn import plotting
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import os
import json

groupdir = os.environ.get("GROUPDIR")
# groupdir = '/oak/stanford/groups/russpold/data/ds000030_R1.0.3_preprocessed_0.4.4/task_group_1000_perm/'
homedir = os.environ.get("HOMEDIR")
acmdir = os.environ.get("ACMDIR")

figdir = os.path.join(groupdir,"figures")

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

        # task = 'stopsignal'
        # contrast = 1

        contrastname = contrasts[task][contrast-1]

        ra_fwe_pos = os.path.join(groupdir,task,'cope%i'%contrast,'randomise','thresh_vox_fwe_tstat1.nii.gz')
        ra_fwe_neg = os.path.join(groupdir,task,'cope%i'%(contrast+1),'randomise','thresh_vox_fwe_tstat1.nii.gz')

        acm_pos = os.path.join(acmdir,task,"zstat%i_ACM_0.nii.gz"%contrast)
        acm_neg = os.path.join(acmdir,task,"zstat%i_ACM_0.nii.gz"%(contrast+1))

        title = "%s - %s"%(task,contrastname)
        display = plotting.plot_glass_brain(None)
        display.add_contours(ra_fwe_pos,levels=[0.0000001],filled=True,colors=('r'),alpha=0.3)
        display.add_contours(ra_fwe_neg,levels=[0.0000001],filled=True,colors=('c'),alpha=0.3)
        display.add_contours(ra_fwe_pos,levels=[0.0000001],filled=False,colors=('r'))
        display.add_contours(ra_fwe_neg,levels=[0.0000001],filled=False,colors=('c'))
        # patches = []
        # patches.append(mp.Patch(color='c',label='flame'))
        # patches.append(mp.Patch(color='m',label='ols'))
        # patches.append(mp.Patch(color='g',label='randomise'))
        # legend = plt.legend(loc=0,handles=patches,ncol=3)
        # frame = legend.get_frame()
        # frame.set_facecolor('0.95')
        # for label in legend.get_texts():
        #     label.set_fontsize('small')
        display.title(title,fontsize='small')
        plt.savefig(os.path.join(figdir,"%s_%i_FDR.pdf"%(task,contrast)),bbox_inches='tight')



        title = "%s - %s"%(task,contrastname)
        display = plotting.plot_glass_brain(None)
        if np.sum(nib.load(acm_pos).get_data()>0.1)>0:
            display.add_contours(acm_pos,levels=[0.2],filled=True,colors=('r'),alpha=0.3)
            display.add_contours(acm_pos,levels=[0.2],cmap='autumn')

        if np.sum(nib.load(acm_neg).get_data()>0.1)>0:
            display.add_contours(acm_neg,levels=[0.2],filled=True,colors=('c'),alpha=0.3)
            display.add_contours(acm_neg,levels=[0.2],cmap='winter')

        display.title(title,fontsize='small')
        plt.savefig(os.path.join(figdir,"%s_%i_ACM.pdf"%(task,contrast)),bbox_inches='tight')


        plt.close('all')
