import pandas as pd
import numpy as np
import os
import shutil


def create_confounds(confounds_in, eventsdir):

    confounds = np.array(confounds_in)
    if np.sum(confounds == 'n/a') > 0:
        confounds[confounds == 'n/a'] = 0
    confounds = confounds.astype(float)
    confoundsfile = os.path.join(eventsdir, 'bold_confounds.tsv')
    np.savetxt(confoundsfile, np.array(confounds), '%5.3f')

    return confoundsfile


def create_ev(dataframe, out_dir, out_name, duration=1, amplitude=1):
    # amplitude: value or variable name
    # duration: value or variable name
    dataframe = dataframe[dataframe.onset.notnull()]
    onsets = [round(float(x), ndigits=3) for x in dataframe.onset.tolist()]
    if isinstance(duration, float) or isinstance(duration, int):
        dur = [duration] * len(onsets)
    elif isinstance(duration, str):
        dur = [round(float(x), ndigits=3) for x in dataframe[duration].tolist()]
    if isinstance(amplitude, float) or isinstance(amplitude, int):
        weights = [amplitude] * len(onsets)
    elif isinstance(amplitude, str):
        weights = dataframe[amplitude] - np.mean(dataframe[amplitude])
        weights = [round(float(x), ndigits=3) for x in weights.tolist()]
    EV = pd.DataFrame({"0": onsets, "1": dur, "2": weights})
    EVfile = os.path.join(out_dir, out_name + ".txt")
    EV.to_csv(EVfile, sep="\t", header=False, index=False)
    return EVfile


def create_ev_task(eventsfile, eventsdir, task):

    events = pd.read_csv(eventsfile, sep="\t", na_values='n/a')
    EVfiles = []

    if task == 'stopsignal':

        nEV = 6
        ortho = {x: {y: 0 for y in range(1, nEV + 1)} for x in range(1, nEV + 1)}

        go_table = events[(events.TrialOutcome == "SuccessfulGo")]
        EVfiles.append(create_ev(go_table, out_name="GO",
                                 duration=1, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(go_table, out_name="GO_rt",
                                 duration='ReactionTime', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles) - 1] = 1
        ortho[len(EVfiles)][0] = 1

        stop_success_table = events[(events.TrialOutcome == "SuccessfulStop")]
        EVfiles.append(create_ev(stop_success_table, out_name="STOP_SUCCESS",
                                 duration=1, amplitude=1, out_dir=eventsdir))

        stop_unsuccess_table = events[(events.TrialOutcome == "UnsuccessfulStop")]
        EVfiles.append(create_ev(stop_unsuccess_table, out_name="STOP_UNSUCCESS",
                                 duration=1, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(stop_unsuccess_table, out_name="STOP_UNSUCCESS_rt",
                                 duration='ReactionTime', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles) - 1] = 1
        ortho[len(EVfiles)][0] = 1

        junk_table = events[(events.TrialOutcome == "JUNK")]
        EVfiles.append(create_ev(junk_table, out_name="JUNK",
                                 duration=1, amplitude=1, out_dir=eventsdir))

        if len(EVfiles) != nEV:
            raise ValueError(
                "the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    return {"EVfiles": EVfiles, "orthogonal": ortho}


def create_contrasts(task):

    contrasts = []

    if task == 'stopsignal':

        contrasts += [('Go', 'T', ['GO'], [1])]
        contrasts += [('GoRT', 'T', ['GO_rt'], [1])]
        contrasts += [('StopSuccess', 'T', ['STOP_SUCCESS'], [1])]
        contrasts += [('StopUnsuccess', 'T', ['STOP_UNSUCCESS'], [1])]
        contrasts += [('StopUnsuccessRT', 'T', ['STOP_UNSUCCESS_rt'], [1])]
        contrasts += [('Go-StopSuccess', 'T', ['GO', 'STOP_SUCCESS'], [1, -1])]
        contrasts += [('Go-StopUnsuccess', 'T', ['GO', 'STOP_UNSUCCESS'], [1, -1])]
        contrasts += [('StopSuccess-StopUnsuccess', 'T',
                       ['STOP_SUCCESS', 'STOP_UNSUCCESS'], [1, -1])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s' % con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname, 'T', con[2], [-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg

    return contrasts


def purge_feat(featdir):
    # remove from main feat: cluster results
    content = os.listdir(featdir)
    content = [os.path.join(featdir, x) for x in content]
    remove = ['cluster', 'lmax', '.vol', 'rendered_thresh', 'thresh_zstat']

    # remove from plots dir: all but plots in stats report
    rmfiles = [x for key in remove for x in content if key in x]

    for rmfile in rmfiles:
        if os.path.exists(rmfile):
            os.remove(rmfile)

    shutil.rmtree(os.path.join(featdir, "tsplot"))


def check_exceptions(SUBJECT, TASK):
    gonogo = True

    # following subjects have incomplete conditions: certain conditions where no reaction was registered --> sign of a failed experiment
    elif TASK == 'stopsignal':
        submis = ['sub-50010', 'sub-10527']

    if SUBJECT in submis:
        gonogo = False

    # these subjects have functional scans, but not anatomical --> not preprocessed
    subnoT1 = ['sub-10428', 'sub-10501', 'sub-70035',
               'sub-70036', 'sub-11121', 'sub-10299', 'sub-10971']
    if SUBJECT in subnoT1:
        gonogo = False

    return gonogo
