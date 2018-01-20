import pandas as pd
import numpy as np
import os
import shutil

def create_confounds(confounds_in,eventsdir):

    confounds = np.array(confounds_in)
    if np.sum(confounds=='n/a')>0:
        confounds[confounds=='n/a']=0
    confounds = confounds.astype(float)
    confoundsfile = os.path.join(eventsdir,'bold_confounds.tsv')
    np.savetxt(confoundsfile,np.array(confounds), '%5.3f')

    return confoundsfile

def create_ev(dataframe,out_dir,out_name,duration=1,amplitude=1):
    # amplitude: value or variable name
    # duration: value or variable name
    dataframe = dataframe[dataframe.onset.notnull()]
    onsets = [round(float(x),ndigits=3) for x in dataframe.onset.tolist()]
    if isinstance(duration,float) or isinstance(duration,int):
        dur = [duration]*len(onsets)
    elif isinstance(duration,str):
        dur = [round(float(x),ndigits=3) for x in dataframe[duration].tolist()]
    if isinstance(amplitude,float) or isinstance(amplitude,int):
        weights = [amplitude]*len(onsets)
    elif isinstance(amplitude,str):
        weights = dataframe[amplitude] - np.mean(dataframe[amplitude])
        weights = [round(float(x),ndigits=3) for x in weights.tolist()]
    EV = pd.DataFrame({"0":onsets,"1":dur,"2":weights})
    EVfile = os.path.join(out_dir,out_name+".txt")
    EV.to_csv(EVfile,sep="\t",header=False,index=False)
    return EVfile

def create_ev_task(eventsfile,eventsdir,task):

    events = pd.read_csv(eventsfile,sep="\t",na_values='n/a')
    EVfiles = []

    if task == 'pamret':

        nEV=9
        ortho = {x: {y:0 for y in range(1,nEV+1)} for x in range(1,nEV+1)}

        truepos_table = events[(events.trial_type=='CORRECTLY') & ((events.response_str=='MAYBE_CORRECT') | (events.response_str=="SURE_CORRECT"))]
        EVfiles.append(create_ev(truepos_table, out_name="TRUEPOS", duration=3, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(truepos_table, out_name="TRUEPOS_rt", duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        trueneg_table = events[(events.trial_type=='INCORRECTLY') & ((events.response_str=='MAYBE_INCORRECT') | (events.response_str=="SURE_INCORRECT"))]
        EVfiles.append(create_ev(trueneg_table, out_name="TRUENEG", duration=3, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(trueneg_table, out_name="TRUENEG_rt", duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        falsepos_table = events[(events.trial_type=='INCORRECTLY') & ((events.response_str=='MAYBE_CORRECT') | (events.response_str=="SURE_CORRECT"))]
        EVfiles.append(create_ev(falsepos_table, out_name="FALSEPOS", duration=3, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(falsepos_table, out_name="FALSEPOS_rt",duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        falseneg_table = events[(events.trial_type=='CORRECTLY') & ((events.response_str=='MAYBE_INCORRECT') | (events.response_str=="SURE_INCORRECT"))]
        EVfiles.append(create_ev(falseneg_table, out_name="FALSENEG", duration=3, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(falseneg_table, out_name="FALSENEG_rt", duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        control_table = events[(events.trial_type=='CONTROL')]
        EVfiles.append(create_ev(control_table, out_name="CONTROL", duration=3, amplitude=1, out_dir=eventsdir))

        if len(EVfiles)!=nEV:
            raise ValueError("the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    if task == 'bart':

        nEV=9
        ortho = {x: {y:0 for y in range(1,nEV+1)} for x in range(1,nEV+1)}

        accept_table = events[(events.trial_type=="BALOON") & (events.action=="ACCEPT")]
        EVfiles.append(create_ev(accept_table, out_name="ACCEPT", duration=0.5, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(accept_table, out_name="ACCEPT_rt", duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1
        EVfiles.append(create_ev(accept_table, out_name="ACCEPT_parametric", duration=0.5, amplitude='trial_cumulative_value', out_dir=eventsdir))

        control_table = events[(events.trial_type=="CONTROL")]
        EVfiles.append(create_ev(control_table, out_name="CONTROL", duration=0.5, amplitude=1, out_dir=eventsdir))

        explode_table = events[(events.action=="EXPLODE")]
        EVfiles.append(create_ev(explode_table, out_name="EXPLODE", duration=0.5, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(explode_table, out_name="EXPLODE_parametric", duration=0.5, amplitude='trial_cumulative_value', out_dir=eventsdir))

        reject_table = events[(events.action=="CASHOUT")]
        EVfiles.append(create_ev(reject_table, out_name="REJECT", duration=0.5, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(reject_table, out_name="REJECT_rt", duration='reaction_time', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1
        EVfiles.append(create_ev(reject_table, out_name="REJECT_parametric", duration=0.5, amplitude='trial_cumulative_value', out_dir=eventsdir))

        if len(EVfiles)!=nEV:
            raise ValueError("the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    if task == 'scap':

        nEV=25
        ortho = {x: {y:0 for y in range(1,nEV+1)} for x in range(1,nEV+1)}

        for load in [1,3,5,7]:
            for delay in [1.5,3,4.5]:
                res_table = events[(events.ResponseAccuracy=="CORRECT") & (events.Load==load) & (events.Delay==delay)]
                res_table['onset'] = res_table['onset']+delay
                EVfiles.append(create_ev(res_table, out_name="LOAD%s_DELAY%s"%(str(load),str(delay)), duration=3, amplitude=1, out_dir=eventsdir))
                EVfiles.append(create_ev(res_table, out_name="LOAD%s_DELAY%s_rt"%(str(load),str(delay)), duration="ReactionTime", amplitude=1, out_dir=eventsdir))
                ortho[len(EVfiles)][len(EVfiles)-1]=1
                ortho[len(EVfiles)][0]=1

        incorrect_table = events[(events.ResponseAccuracy=='INCORRECT')]
        EVfiles.append(create_ev(incorrect_table,out_name="INCORRECT",duration=3,amplitude=1,out_dir=eventsdir))

        if len(EVfiles)!=nEV:
            raise ValueError("the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    if task == 'stopsignal':

        nEV=6
        ortho = {x: {y:0 for y in range(1,nEV+1)} for x in range(1,nEV+1)}

        go_table = events[(events.TrialOutcome=="SuccessfulGo")]
        EVfiles.append(create_ev(go_table, out_name="GO", duration=1, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(go_table, out_name="GO_rt", duration='ReactionTime', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        stop_success_table = events[(events.TrialOutcome=="SuccessfulStop")]
        EVfiles.append(create_ev(stop_success_table, out_name="STOP_SUCCESS", duration=1, amplitude=1, out_dir=eventsdir))

        stop_unsuccess_table = events[(events.TrialOutcome=="UnsuccessfulStop")]
        EVfiles.append(create_ev(stop_unsuccess_table, out_name="STOP_UNSUCCESS", duration=1, amplitude=1, out_dir=eventsdir))
        EVfiles.append(create_ev(stop_unsuccess_table, out_name="STOP_UNSUCCESS_rt", duration='ReactionTime', amplitude=1, out_dir=eventsdir))
        ortho[len(EVfiles)][len(EVfiles)-1]=1
        ortho[len(EVfiles)][0]=1

        junk_table = events[(events.TrialOutcome=="JUNK")]
        EVfiles.append(create_ev(junk_table, out_name="JUNK", duration=1, amplitude=1, out_dir=eventsdir))

        if len(EVfiles)!=nEV:
            raise ValueError("the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    if task == 'taskswitch':
        nEV=16

        ortho = {x: {y:0 for y in range(1,nEV+1)} for x in range(1,nEV+1)}
        for congruent in ["CONGRUENT","INCONGRUENT"]:
            for switch in ["SWITCH","NOSWITCH"]:
                for CSI in ["SHORT","LONG"]:
                    res_table = events[(events.Switching==switch) & (events.CSI==CSI) & (events.Congruency==congruent) & (events.ReactionTime.notnull()) & (events.CorrectResp != 0)]
                    EVfiles.append(create_ev(res_table, out_name="_".join([congruent,switch,CSI]), duration=1, amplitude=1, out_dir=eventsdir))
                    EVfiles.append(create_ev(res_table, out_name="_".join([congruent,switch,CSI])+"_rt", duration="ReactionTime", amplitude=1, out_dir=eventsdir))
                    ortho[len(EVfiles)][len(EVfiles)-1]=1
                    ortho[len(EVfiles)][0]=1


        if len(EVfiles)!=nEV:
            raise ValueError("the number of evfiles is not equal to the number of orthogonalisations, please check.")

        EVfiles = [x for x in EVfiles if os.path.getsize(x) > 0]

    return {"EVfiles":EVfiles,"orthogonal":ortho}

def create_contrasts(task):

    contrasts = []

    if task == 'pamret':

        contrasts += [('All','T',['TRUEPOS','TRUENEG','FALSEPOS','FALSENEG'],[1,1,1,1])]
        contrasts += [('All_RT','T',['TRUEPOS_rt','TRUENEG_rt','FALSEPOS_rt','FALSENEG_rt'],[1,1,1,1])]
        contrasts += [('Correct','T',['TRUEPOS','TRUENEG',],[1,1])]
        contrasts += [('Incorrect','T',['FALSEPOS','FALSENEG'],[1,1])]
        contrasts += [('TruePos','T',['TRUEPOS'],[1])]
        contrasts += [('TrueNeg','T',['TRUENEG'],[1])]
        contrasts += [('FalsePos','T',['FALSEPOS'],[1])]
        contrasts += [('FalseNeg','T',['FALSENEG'],[1])]
        contrasts += [('TruePos_RT','T',['TRUEPOS_rt'],[1])]
        contrasts += [('TrueNeg_RT','T',['TRUENEG_rt'],[1])]
        contrasts += [('FalsePos_RT','T',['FALSEPOS_rt'],[1])]
        contrasts += [('FalseNeg_RT','T',['FALSENEG_rt'],[1])]
        contrasts += [('Control','T',['CONTROL'],[1])]

        contrasts += [('TruePos-TrueNeg','T',['TRUEPOS','TRUENEG'],[1,-1])]
        contrasts += [('FalsePos-FalseNeg','T',['FALSEPOS','FALSENEG'],[1,-1])]
        contrasts += [('TruePos-FalsePos','T',['TRUEPOS','FALSEPOS'],[1,-1])]
        contrasts += [('TrueNeg-FalseNeg','T',['TRUENEG','FALSENEG'],[1,-1])]
        contrasts += [('Corr-Incorr','T',['TRUEPOS','TRUENEG','FALSEPOS','FALSENEG'],[1,1,-1,-1])]
        contrasts += [('Correct-Control','T',['TRUEPOS','TRUENEG','CONTROL'],[0.5,0.5,-1])]
        contrasts += [('Incorrect-Control','T',['FALSEPOS','FALSENEG','CONTROL'],[0.5,0.5,-1])]
        contrasts += [('TruePos-Control','T',['FALSEPOS','CONTROL'],[1,-1])]
        contrasts += [('TrueNeg-Control','T',['FALSENEG','CONTROL'],[1,-1])]
        contrasts += [('FalsePos-Control','T',['FALSEPOS','CONTROL'],[1,-1])]
        contrasts += [('FalseNeg-Control','T',['FALSENEG','CONTROL'],[1,-1])]
        contrasts += [('All-Control','T',['TRUEPOS','TRUENEG','FALSEPOS','FALSENEG','CONTROL'],[0.25,0.25,0.25,0.25,-1])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s'%con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname,'T',con[2],[-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg

    if task == 'bart':

        contrasts += [('Accept','T',['ACCEPT'],[1])]
        contrasts += [('AcceptRT','T',['ACCEPT_rt'],[1])]
        contrasts += [('AcceptParametric','T',['ACCEPT_parametric'],[1])]
        contrasts += [('Control','T',['CONTROL'],[1])]
        contrasts += [('Explode','T',['EXPLODE'],[1])]
        contrasts += [('ExplodeParametric','T',['EXPLODE_parametric'],[1])]
        contrasts += [('Reject','T',['REJECT'],[1])]
        contrasts += [('RejectRT','T',['REJECT_rt'],[1])]
        contrasts += [('RejectParametric','T',['REJECT_parametric'],[1])]

        contrasts += [('AcceptParam-ExplodeParam','T',['ACCEPT_parametric','EXPLODE_parametric'],[1,-1])]
        contrasts += [('AcceptParam-RejectParam','T',['ACCEPT_parametric','REJECT_parametric'],[1,-1])]
        contrasts += [('Explode-Reject','T',['EXPLODE','REJECT'],[1,-1])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s'%con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname,'T',con[2],[-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg

    if task == 'scap':

        contrasts += [('All','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5',
        'LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[1]*12)]
        contrasts += [('All_rt','T',['LOAD1_DELAY1.5_rt', 'LOAD1_DELAY3_rt', 'LOAD1_DELAY4.5_rt',
        'LOAD3_DELAY1.5_rt', 'LOAD3_DELAY3_rt', 'LOAD3_DELAY4.5_rt',
        'LOAD5_DELAY1.5_rt', 'LOAD5_DELAY3_rt', 'LOAD5_DELAY4.5_rt',
        'LOAD7_DELAY1.5_rt', 'LOAD7_DELAY3_rt', 'LOAD7_DELAY4.5_rt'],[1]*12)]
        contrasts += [('Load1','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5'],[1]*3)]
        contrasts += [('Load3','T',['LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5'],[1]*3)]
        contrasts += [('Load5','T',['LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5'],[1]*3)]
        contrasts += [('Load7','T',['LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[1]*3)]
        contrasts += [('Delay1.5','T',['LOAD1_DELAY1.5', 'LOAD3_DELAY1.5','LOAD5_DELAY1.5','LOAD7_DELAY1.5'],[1]*4)]
        contrasts += [('Delay3','T',['LOAD1_DELAY3', 'LOAD3_DELAY3','LOAD5_DELAY3','LOAD7_DELAY3'],[1]*4)]
        contrasts += [('Delay4.5','T',['LOAD1_DELAY4.5', 'LOAD3_DELAY4.5','LOAD5_DELAY4.5','LOAD7_DELAY4.5'],[1]*4)]

        contrasts += [('LinearUp_load','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5',
        'LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[-3]*3+[-1]*3+[1]*3+[3]*3)]
        contrasts += [('LinearUp_delay','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5',
        'LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[-1,0,1]*4)]

        contrasts += [('Load3-load1','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Load5-load1','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Load7-load1','T',['LOAD1_DELAY1.5', 'LOAD1_DELAY3', 'LOAD1_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Load5-load3','T',['LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5',
        'LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'LOAD5_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Load7-load3','T',['LOAD3_DELAY1.5', 'LOAD3_DELAY3', 'LOAD3_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Load7-load5','T',['LOAD5_DELAY1.5', 'LOAD5_DELAY3', 'L]OAD_5_DELAY4.5',
        'LOAD7_DELAY1.5', 'LOAD7_DELAY3', 'LOAD7_DELAY4.5'],[-1,-1,-1,1,1,1])]
        contrasts += [('Delay4_5-delay1_5','T',['LOAD1_DELAY1.5', 'LOAD3_DELAY1.5','LOAD5_DELAY1.5','LOAD7_DELAY1.5',
        'LOAD1_DELAY4.5', 'LOAD3_DELAY4.5','LOAD5_DELAY4.5','LOAD7_DELAY4.5'],[-1,-1,-1,-1,1,1,1,1])]
        contrasts += [('Delay3-delay1_5','T',['LOAD1_DELAY1.5', 'LOAD3_DELAY1.5','LOAD5_DELAY1.5','LOAD7_DELAY1.5',
        'LOAD1_DELAY3', 'LOAD3_DELAY3','LOAD5_DELAY3','LOAD7_DELAY3'],[-1,-1,-1,-1,1,1,1,1])]
        contrasts += [('Delay4_5-delay3','T',['LOAD1_DELAY3', 'LOAD3_DELAY3','LOAD5_DELAY3','LOAD7_DELAY3',
        'LOAD1_DELAY4.5', 'LOAD3_DELAY4.5','LOAD5_DELAY4.5','LOAD7_DELAY4.5'],[-1,-1,-1,-1,1,1,1,1])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s'%con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname,'T',con[2],[-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg

    if task == 'stopsignal':

        contrasts += [('Go','T',['GO'],[1])]
        contrasts += [('GoRT','T',['GO_rt'],[1])]
        contrasts += [('StopSuccess','T',['STOP_SUCCESS'],[1])]
        contrasts += [('StopUnsuccess','T',['STOP_UNSUCCESS'],[1])]
        contrasts += [('StopUnsuccessRT','T',['STOP_UNSUCCESS_rt'],[1])]
        contrasts += [('Go-StopSuccess','T',['GO','STOP_SUCCESS'],[1,-1])]
        contrasts += [('Go-StopUnsuccess','T',['GO','STOP_UNSUCCESS'],[1,-1])]
        contrasts += [('StopSuccess-StopUnsuccess','T',['STOP_SUCCESS','STOP_UNSUCCESS'],[1,-1])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s'%con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname,'T',con[2],[-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg
    if task == 'taskswitch':

        contrasts += [('ALL','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[1,1,1,1,1,1,1,1])]
        contrasts += [('ALL_rt','T',
        ['CONGRUENT_NOSWITCH_LONG_rt','CONGRUENT_NOSWITCH_SHORT_rt','CONGRUENT_SWITCH_LONG_rt','CONGRUENT_SWITCH_SHORT_rt',
        'INCONGRUENT_NOSWITCH_LONG_rt','INCONGRUENT_NOSWITCH_SHORT_rt','INCONGRUENT_SWITCH_LONG_rt','INCONGRUENT_SWITCH_SHORT_rt'],[1,1,1,1,1,1,1,1])]

        for congruent in ["CONGRUENT","INCONGRUENT"]:
            for switch in ["SWITCH","NOSWITCH"]:
                for CSI in ["SHORT","LONG"]:
                    contrasts += [("_".join([congruent,switch,CSI]),'T',["_".join([congruent,switch,CSI])],[1])]
                    contrasts += [("_".join([congruent,switch,CSI])+"_rt",'T',["_".join([congruent,switch,CSI])+"_rt"],[1])]

        contrasts += [('CONGRUENT-INCONGRUENT','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[1,1,1,1,-1,-1,-1,-1])]
        contrasts += [('SWITCH-NOSWITCH','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[-1,-1,1,1,-1,-1,1,1])]
        contrasts += [('SWITCH-NOSWITCH_SHORT','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[0,-1,0,1,0,-1,0,1])]
        contrasts += [('SWITCH-NOSWITCH_LONG','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[-1,0,1,0,-1,0,1,0])]
        contrasts += [('CONGRUENT-INCONGRUENT_SHORT','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[0,1,0,1,0,-1,0,-1])]
        contrasts += [('CONGRUENT-INCONGRUENT_LONG','T',
        ['CONGRUENT_NOSWITCH_LONG','CONGRUENT_NOSWITCH_SHORT','CONGRUENT_SWITCH_LONG','CONGRUENT_SWITCH_SHORT',
        'INCONGRUENT_NOSWITCH_LONG','INCONGRUENT_NOSWITCH_SHORT','INCONGRUENT_SWITCH_LONG','INCONGRUENT_SWITCH_SHORT'],[1,0,1,0,-1,0,-1,0])]

        # add negative
        repl_w_neg = []
        for con in contrasts:
            if not '-' in con[0]:
                newname = 'neg_%s'%con[0]
            else:
                newname = "-".join(con[0].split("-")[::-1])
            new = (newname,'T',con[2],[-x for x in con[3]])
            repl_w_neg.append(con)
            repl_w_neg.append(new)

        contrasts = repl_w_neg

    return contrasts


def purge_feat(featdir):
    # remove from main feat: cluster results
    content = os.listdir(featdir)
    content = [os.path.join(featdir,x) for x in content]
    remove = ['cluster','lmax','.vol','rendered_thresh','thresh_zstat']

    # remove from plots dir: all but plots in stats report
    rmfiles = [x for key in remove for x in content if key in x]

    for rmfile in rmfiles:
        if os.path.exists(rmfile):
            os.remove(rmfile)

    shutil.rmtree(os.path.join(featdir,"tsplot"))

def check_exceptions(SUBJECT,TASK):
    gonogo = True

    # following subjects have incomplete conditions: certain conditions where no reaction was registered --> sign of a failed experiment
    if TASK == 'pamret':
        submis = ['sub-11104','sub-10557','sub-10530','sub-60056','sub-70058','sub-10565','sub-50053','sub-60060','sub-50051']
    if TASK == 'scap':
        submis = ['sub-50004','sub-10788','sub-50064','sub-60073','sub-10680','sub-10998','sub-70022','sub-60068','sub-70055','sub-70048','sub-50014','sub-50069','sub-10171','sub-70072','sub-50022','sub-10159']
    elif TASK == 'taskswitch':
        submis = ['sub-50004','sub-70048','sub-10235','sub-60089']
    elif TASK == 'stopsignal':
        submis = ['sub-50010','sub-10527']
    elif TASK == 'bart':
        submis = ['sub-50010','sub-50069']

    if SUBJECT in submis:
        gonogo = False

    # these subjects have functional scans, but not anatomical --> not preprocessed
    subnoT1 = ['sub-10428','sub-10501','sub-70035','sub-70036','sub-11121','sub-10299','sub-10971']
    if SUBJECT in subnoT1:
        gonogo = False

    return gonogo
