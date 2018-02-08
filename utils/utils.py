import pandas as pd
import numpy as np
import os
import shutil


def create_confounds(confounds_in, eventsdir, value=0.0):
    """
    Clears out n/a entries in the BIDS-derivatives confounds file
    and stores it in a format compatible with FSL feat.


    Args:
        confounds_in: path to a bids-derivatives confounds file
        eventsdir: path to the events directory of FSL feat
        value: replacement of n/a entries in ``confounds_in``.

    Returns:
        A string pointing to the new confounds file

    """
    confounds = np.array(confounds_in)
    confounds[confounds == 'n/a'] = value
    confounds = confounds.astype(float)
    confoundsfile = os.path.join(eventsdir, 'bold_confounds.tsv')
    np.savetxt(confoundsfile, np.array(confounds), '%5.3f')
    return confoundsfile


def create_ev(dataframe, out_dir, out_name, duration=1, amplitude=1):
    """
    Adapt a BIDS-compliant events file to a format compatible with FSL feat

    Args:
        dataframe: events file from BIDS spec
        out_dir: path where new events file will be stored
        out_name: filename for the new events file
        amplitude: value or variable name
        duration: value or variable name

    Returns:
        Full path to the new events file

    """
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
    EVfile = os.path.join(out_dir, '%s.txt' % out_name)
    EV.to_csv(EVfile, sep="\t", header=False, index=False)
    return EVfile


def create_ev_task(eventsfile, eventsdir, task='stopsignal'):
    """
    Create events file for the stopsignal task
    """

    # Break early when things don't look alright
    if task != 'stopsignal':
        raise NotImplementedError(
            'This function was not designed for tasks other than "stopsignal". '
            'Task "%s" cannot be processed' % task)

    events = pd.read_csv(eventsfile, sep="\t", na_values='n/a')
    EVfiles = []

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
            "the number of evfiles is not equal to the number "
            "of orthogonalisations, please check.")

    EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    return {"EVfiles": EVfiles, "orthogonal": ortho}


def create_contrasts(task):

    # Break early when things don't look alright
    if task != 'stopsignal':
        raise NotImplementedError(
            'This function was not designed for tasks other than "stopsignal". '
            'Task "%s" cannot be processed' % task)

    contrasts = []
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
        if '-' not in con[0]:
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


def check_exceptions(subject_id, task_id):
    """
    Blacklist certain participants. Some do not have anatomical data,
    others have incomplete conditions
    """

    # these subjects have functional scans,
    # but not anatomical --> not preprocessed
    blacklist = ['sub-10428', 'sub-10501', 'sub-70035',
                 'sub-70036', 'sub-11121', 'sub-10299',
                 'sub-10971']

    # following subjects have incomplete conditions: certain conditions
    # where no reaction was registered --> sign of a failed experiment
    if task_id == 'stopsignal':
        blacklist += ['sub-50010', 'sub-10527']

    return subject_id not in blacklist
