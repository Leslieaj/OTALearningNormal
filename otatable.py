# The definitions on the OTA observation table.

import copy
from ota import Timedword, ResetTimedword, is_valid_rtws, dRTWs_to_lRTWs, lRTWs_to_DTWs

class Element(object):
    """The definition of the element in OTA observation table.
    """
    def __init__(self, tws=[], value=[], suffixes_resets=[]):
        self.tws = tws or []
        self.value = value or []
        self.suffixes_resets = suffixes_resets or []
    
    def __eq__(self, element):
        if self.tws == element.tws and self.value == element.value:
            return True
        else:
            return False

    def get_tws_e(self, e):
        tws_e = [tw for tw in self.tws]
        if len(e) == 0:
            return tws_e
        else:
            for tw in e:
                tws_e.append(tw)
            return tws_e

    def row(self):
        return self.value
    
    def whichstate(self):
        state_name = ""
        for v in self.value:
            state_name = state_name+str(v)
        return state_name

    def show(self):
        return [tw.show() for tw in self.tws], self.value, self.suffixes_resets

class OTATable(object):
    """The definition of OTA observation table.
    """
    def __init__(self, S = None, R = None, E=[]):
        self.S = S
        self.R = R
        self.E = E #if E is empty, it means that there is an empty action in E.
    
    def is_prepared(self, ota):
        flag_closed, new_S, new_R, move = self.is_closed()
        flag_consistent, new_a, new_e_index = self.is_consistent()
        flag_evid_closed, new_added = self.is_evidence_closed(ota)
        #if flag_closed == True and flag_consistent == True: #and flag_evid_closed == True:
        if flag_closed == True and flag_consistent == True and flag_evid_closed == True:
            return True
        else:
            return False
    
    def is_closed(self):
        """ 1. determine whether the table is closed.
               For each r in R there exists s in S such that row(s) = row(r).
            2. return four values, the first one is a flag to show closed or not, 
               the second one is the new S and the third one is the new R,
               the last one is the element moved from R to S.
        """
        new_S = [s for s in self.S]
        new_R = [r for r in self.R]
        new_S_rows = [s.row() for s in new_S]
        move = None
        for r in self.R:
            flag = False
            for s in self.S:
                if r.row() == s.row():
                    flag = True
                    break
            if flag == False:
                if r.row() not in new_S_rows:
                    new_S.append(r)
                    new_R.remove(r)
                    move = copy.deepcopy(r)
                    break
                    #new_S_rows = [s.row() for s in new_S]
        if len(new_S) > len(self.S):
            return False, new_S, new_R, move
        else:
            return True, new_S, new_R, move  

    def is_consistent(self):
        """Determine whether the table is consistent.
            (if tws1,tws2 in S U R, if a in sigma* tws1+a, tws2+a in S U R and row(tws1) = row(tws2), 
            then row(tws1+a) = row(tws2+a))
        """
        flag = True
        new_a = None
        new_e_index = None
        table_element = [s for s in self.S] + [r for r in self.R]
        for i in range(0, len(table_element)-1):
            for j in range(i+1, len(table_element)):
                if table_element[i].row() == table_element[j].row():
                    temp_elements1 = []
                    temp_elements2 = []
                    #print len(table_element[2].tws), [tw.show() for tw in table_element[2].tws]
                    for element in table_element:
                        #print "element", [tw.show() for tw in element.tws]
                        if is_prefix(element.tws, table_element[i].tws):
                            new_element1 = Element(delete_prefix(element.tws, table_element[i].tws), [v for v in element.value], []) #-----------todo---------
                            temp_elements1.append(new_element1)
                        if is_prefix(element.tws, table_element[j].tws):
                            #print "e2", [tw.show() for tw in element.tws]
                            new_element2 = Element(delete_prefix(element.tws, table_element[j].tws), [v for v in element.value], []) #-----------todo---------
                            temp_elements2.append(new_element2)
                    for e1 in temp_elements1:
                        for e2 in temp_elements2:
                            #print [tw.show() for tw in e1.tws], [tw.show() for tw in e2.tws]
                            #if len(e1.tws) == 1 and len(e2.tws) == 1 and e1.tws == e2.tws:
                            if len(e1.tws) == 1 and len(e2.tws) == 1 and e1.tws[0].action == e2.tws[0].action and e1.tws[0].time == e2.tws[0].time:
                                if e1.row() == e2.row():
                                    pass
                                else:
                                    flag = False
                                    new_a = e1.tws
                                    for k in range(0, len(e1.value)):
                                        if e1.value[k] != e2.value[k]:
                                            new_e_index = k
                                            reset = e1.tws[0].reset
                                            return flag, new_a, new_e_index, i, j, reset
        return flag, new_a, new_e_index, i, j, True

    def is_evidence_closed(self, ota):
        """Determine whether the table is evidence-closed.
        """
        flag = True
        table_tws = [s.tws for s in self.S] + [r.tws for r in self.R]
        new_added = []
        for s in self.S:
            #local_s = dRTWs_to_lRTWs(s.tws)
            local_s = s.tws
            current_location_name = ota.run_resettimedwords(local_s)
            for e in self.E:
                temp_e = []
                current_location = copy.deepcopy(current_location_name)
                reset = True
                clock_valuation = 0
                if len(s.tws) > 0:
                    reset = local_s[len(local_s)-1].reset
                    clock_valuation = local_s[len(local_s)-1].time
                for tw in e:
                    new_timedword = Timedword(tw.action,tw.time)
                    if reset == False and new_timedword.time < clock_valuation:
                        temp_e.append(ResetTimedword(tw.action,tw.time,True))
                        current_location = ota.sink_name
                        clock_valuation = 0
                        break
                    else:
                        for otatran in ota.trans:
                            if otatran.source == current_location and otatran.is_pass(new_timedword):
                                new_resettimedword = ResetTimedword(tw.action,tw.time,otatran.reset)
                                temp_e.append(new_resettimedword)
                                clock_valuation = new_timedword.time
                                reset = otatran.reset
                                if reset == True:
                                    clock_valuation = 0
                                current_location = otatran.target
                                break
                temp_se = [rtw for rtw in s.tws] + [rtw for rtw in temp_e]
                prefs = prefixes(temp_se)
                for pref in prefs:
                    if pref not in table_tws:
                        table_tws.append(pref)
                        #table_tws = [tws for tws in table_tws] + [pref]
                        new_tws = [tws for tws in pref]
                        new_element = Element(new_tws,[]) #---------------todo------------------
                        new_added.append(new_element)
        if len(new_added) > 0:
            flag = False
        return flag, new_added

    def show(self):
        print("new_S:"+str(len(self.S)))
        for s in self.S:
            print(s.tws, s.row(), s.suffixes_resets)
        print("new_R:"+str(len(self.R)))
        for r in self.R:
            print(r.tws, r.row(), r.suffixes_resets)
        print("new_E:"+str(len(self.E)))
        for e in self.E:
            print(e)

def make_closed(new_S, new_R, move, table, sigma, ota):
    """Make table closed.
    """
    new_E = table.E
    closed_table = OTATable(new_S, new_R, new_E)
    table_tws = [s.tws for s in closed_table.S] + [r.tws for r in closed_table.R]
    temp_resets = [[]]
    for i in range(0,len(sigma)):
        new_rtw_n = ResetTimedword(sigma[i], 0, False)
        new_rtw_r = ResetTimedword(sigma[i], 0, True)
        new_situations = []
        for situation in temp_resets:
            temp = copy.deepcopy(situation)
            temp_n = temp + [new_rtw_n]
            temp_r = temp + [new_rtw_r]
            new_situations.append(temp_r)
            new_situations.append(temp_n)
        temp_resets = new_situations
    #return temp_resets
    OTAtables = []
    for situation in temp_resets:
        new_rs = []
        for new_rtw in situation:
            new_r = [tw for tw in move.tws] + [new_rtw]
            if new_r not in table_tws:
                new_rs.append(Element(new_r,[],[]))
        temp_R = [r for r in new_R] + new_rs
        temp_table = OTATable(new_S, temp_R, new_E)
        OTAtables.append(temp_table)
    #return OTAtables
    #guess the resets of suffixes for each prefix and fill
    OTAtables_after_guessing_resets = []
    for otatable in OTAtables:
        new_r_start_index = len(new_R)
        new_r_end_index = len(otatable.R)
        temp_otatables = [otatable]
        #print(new_r_start_index, new_r_end_index)
        for i in range(new_r_start_index, new_r_end_index):
            resets_situtations = guess_resets_in_suffixes(otatable)
            new_tables = []
            for j in range(0, len(resets_situtations)):
                for temp_table in temp_otatables:
                    new_table = copy.deepcopy(temp_table)
                    temp_otatable = OTATable(new_table.S, new_table.R, new_table.E)
                    temp_otatable.R[i].suffixes_resets = resets_situtations[j]
                    new_table = copy.deepcopy(temp_otatable)
                    if True == fill(new_table.R[i],new_table.E,ota):
                        new_tables.append(new_table)
            temp_otatables = [tb for tb in new_tables]
            #print("a", len(temp_otatables))
        OTAtables_after_guessing_resets = OTAtables_after_guessing_resets + temp_otatables
        #print("b", len(OTAtables_after_guessing_resets))
    return OTAtables_after_guessing_resets

def make_consistent(new_a, new_e_index, fix_reset_i, fix_reset_j, reset, table, sigma, ota):
    """Make table consistent.
    """
    new_E = [tws for tws in table.E]
    new_e = [Timedword(tw.action,tw.time) for tw in new_a]
    if new_e_index > 0:
        e = table.E[new_e_index-1]
        new_e.extend(e)
    new_E.append(new_e)
    new_table = OTATable(table.S,table.R,new_E)
    temp_suffixes_resets = guess_resets_in_newsuffix(new_table)
    OTAtables = []
    for situation in temp_suffixes_resets:
        temp_situation = []
        for resets in situation:
            temp_situation.extend(resets)
        if temp_situation[fix_reset_i] == temp_situation[fix_reset_j] and temp_situation[fix_reset_i] == reset:
            temp_table = copy.deepcopy(table)
            temp_table.E = copy.deepcopy(new_E)
            flag_valid = True
            for i in range(0,len(situation)):
                if i < len(table.S):
                    temp_table.S[i].suffixes_resets.append(situation[i])
                    if True == fill(temp_table.S[i],temp_table.E, ota):
                        pass
                    else:
                        flag_valid = False
                else:
                    temp_table.R[i-len(temp_table.S)].suffixes_resets.append(situation[i])
                    if True == fill(temp_table.R[i-len(temp_table.S)],temp_table.E, ota):
                        pass
                    else:
                        flag_valid = False
            if flag_valid == True:
                OTAtables.append(temp_table)
    return OTAtables

def prefixes(tws):
    """Return the prefixes of a timedwords. [tws1, tws2, tws3, ..., twsn]
    """
    prefixes = []
    for i in range(1, len(tws)+1):
        temp_tws = tws[:i]
        prefixes.append(temp_tws)
    return prefixes

def is_prefix(tws, pref):
    """Determine whether the pref is a prefix of the timedwords tws
    """
    if len(pref) == 0:
        return True
    else:
        if len(tws) < len(pref):
            return False
        else:
            for i in range(0, len(pref)):
                if tws[i] == pref[i]:
                    pass
                else:
                    return False
            return True

def delete_prefix(tws, pref):
    """Delete a prefix of timedwords tws, and return the new tws
    """
    if len(pref) == 0:
        return [tw for tw in tws]
    else:
        new_tws = tws[len(pref):]
        return new_tws

def init_table_normal(sigma, ota):
    """Initial tables.
    """
    S = [Element([],[])]
    R = []
    E = []
    for s in S:
        if ota.initstate_name in ota.accept_names:
            s.value.append(1)
        else:
            s.value.append(0)
    tables = [OTATable(S, R, E)]
    for i in range(0, len(sigma)):
        temp_tables = []
        for table in tables:
            new_tw = Timedword(sigma[i], 0)
            for tran in ota.trans:
                if tran.source == ota.initstate_name and tran.is_pass(new_tw):
                    new_rtw_n = ResetTimedword(new_tw.action, new_tw.time, False)
                    new_rtw_r = ResetTimedword(new_tw.action, new_tw.time, True)
                    new_value = []
                    if tran.target in ota.accept_names:
                        new_value = [1]
                    elif tran.target == ota.sink_name:
                        new_value = [-1]
                    else:
                        new_value = [0]
                    new_element_n = Element([new_rtw_n], new_value)
                    new_element_r = Element([new_rtw_r], new_value)
                    temp_R_n = table.R + [new_element_n]
                    temp_R_r = table.R + [new_element_r]
                    new_table_n = OTATable(S, temp_R_n, E)
                    new_table_r = OTATable(S, temp_R_r, E)
                    temp_tables.append(new_table_n)
                    temp_tables.append(new_table_r)
                    break
        tables = temp_tables
    return tables

def guess_resets_in_suffixes(table):
    """Given a table T, before membership querying, we need to guess the reset in the suffixes.
    This method is for one element in S or R. 
    """
    temp_suffixes_resets = []
    length = 0
    for e in table.E:
        length = length + len(e)
    temp_resets = [[]]
    for i in range(0,length):
        temp = []
        for resets_situation in temp_resets:
            temp_R = resets_situation + [True]
            temp_N = resets_situation + [False]
            temp.append(temp_R)
            temp.append(temp_N)
        temp_resets = temp
    for resets_situation in temp_resets:
        index = 0
        suffixes_resets = []
        for e in table.E:
            e_resets = []
            for i in range(index, index+len(e)):
                e_resets.append(resets_situation[i])
            suffixes_resets.append(e_resets)
            index = index + len(e)
        temp_suffixes_resets.append(suffixes_resets)
    return temp_suffixes_resets

def guess_resets_in_newsuffix(table):
    """When making consistent, guess the resets in the new suffix.
    """
    temp_suffixes_resets = []
    new_e_length = len(table.E[len(table.E)-1])
    S_U_R_length = len(table.S) + len(table.R)
    length = S_U_R_length*new_e_length
    temp_resets = [[]]
    for i in range(0,length):
        temp = []
        for resets_situation in temp_resets:
            temp_R = resets_situation + [True]
            temp_N = resets_situation + [False]
            temp.append(temp_R)
            temp.append(temp_N)
        temp_resets = temp
    for resets_situation in temp_resets:
        index = 0
        suffixes_resets = []
        for i in range(0, S_U_R_length):
            e_resets = resets_situation[index : index+new_e_length]
            suffixes_resets.append(e_resets)
            index = index + new_e_length
        temp_suffixes_resets.append(suffixes_resets)
    return temp_suffixes_resets

def guess_ctx_reset(dtws):
    """When receiving a counterexample (delay timed word), guess all resets and return all reset delay timed words as ctx candidates.  
    """
    #ctxs = []
    new_tws = [Timedword(tw.action,tw.time) for tw in dtws]
    ctxs = [[ResetTimedword(new_tws[0].action, new_tws[0].time, False)], [ResetTimedword(new_tws[0].action, new_tws[0].time, True)]]
    for i in range(1, len(new_tws)):
        templist = []
        for rtws in ctxs:
            temp_n = rtws + [ResetTimedword(new_tws[i].action, new_tws[i].time, False)] 
            temp_r = rtws + [ResetTimedword(new_tws[i].action, new_tws[i].time, True)]
            templist.append(temp_n)
            templist.append(temp_r)
        #ctxs = copy.deepcopy(templist)
        ctxs = templist
    return ctxs

def check_guessed_reset(lrtws, table):
    """Given a guessed normalized reset-logical(local)-timed-word, check the reset whether it is suitable to current table.
       If the action and the clock valuation are same to the Element in S U R, however, the resets are diferent, then return False to identicate
       the wrong guess.
    """
    S_U_R = [s for s in table.S] + [r for r in table.R]
    for element in S_U_R:
        for rtw, i in zip(lrtws, range(0, len(lrtws))):
            if i < len(element.tws):
                if rtw.action == element.tws[i].action and rtw.time == element.tws[i].time:
                    if rtw.reset != element.tws[i].reset:
                        return False
                else:
                    break
            else:
                break
    return True

def normalize(tws):
    """Normalize the ctx.
    """
    for rtw in tws:
        if isinstance(rtw.time, int) == True:
            pass
        else:
            integer, frac = str(rtw.time).split('.')
            if frac == '0':
                rtw.time = int(integer)
            else:
                rtw.time = float(integer + '.1')

def build_logical_resettimedwords(element, e, e_index):
    """build a logical reset timedwords based on an element in S,R and a suffix e in E.
    """
    lrtws = [tw for tw in element.tws]
    temp_suffixes_timedwords = [ResetTimedword(tw.action,tw.time, element.suffixes_resets[e_index][j]) for tw, j in zip(e, range(len(e)))]
    lrtws = lrtws + temp_suffixes_timedwords
    flag = is_valid_rtws(lrtws)
    return lrtws, flag

def fill(element, E, ota):
    """Fill an element in S U R.
    """
    local_tws = element.tws
    delay_tws = lRTWs_to_DTWs(local_tws)
    #current_location_name = ota.run_delaytimedwords(delay_tws)
    if len(element.value) == 0:
    #if len(E) == 0:
        f = ota.is_accepted_delay(delay_tws)
        element.value.append(f)
        #return True
    # if current_location_name == ota.sink_name:
    #     for i in range(len(element.value)-1, len(E)):
    #         element.value.append(-1)
    #         return True
    # else:
    for i in range(len(element.value)-1, len(E)):
        lrtws, flag = build_logical_resettimedwords(element, E[i], i)
        if flag == True:
            delay_tws = lRTWs_to_DTWs(lrtws)
            f = ota.is_accepted_delay(delay_tws)
            element.value.append(f)
                #return True
        else:
            return False
    return True

def add_ctx_normal(dtws, table, ota):
    """Given a counterexample ctx, guess the reset, check the reset, for each suitable one, add it and its prefixes to R (except those already present in S and R)
    """
    #print(ctx)
    #print(fix_resets(ctx,ota))
    #local_tws = dRTWs_to_lRTWs(fix_resets(ctx,ota))
    OTAtables = []
    ctxs = guess_ctx_reset(dtws)
    for ctx in ctxs:
        local_tws = dRTWs_to_lRTWs(ctx)
        normalize(local_tws)
        if check_guessed_reset(local_tws, table) == True:
            #print(local_tws)
            pref = prefixes(local_tws)
            S_tws = [s.tws for s in table.S]
            S_R_tws = [s.tws for s in table.S] + [r.tws for r in table.R]
            new_S = [s for s in table.S]
            new_R = [r for r in table.R]
            new_E = [e for e in table.E]
            for tws in pref:
                need_add = True
                for stws in S_R_tws:
                #for stws in S_tws:
                    #if tws_equal(tws, stws):
                    if tws == stws:
                        need_add = False
                        break
                if need_add == True:
                    temp_element = Element(tws,[],[])
                    #fill(temp_element, new_E, ota)
                    new_R.append(temp_element)
            new_OTAtable = OTATable(new_S, new_R, new_E)
            OTAtables.append(new_OTAtable)
    #return OTAtables
    #guess the resets of suffixes for each prefix and fill
    OTAtables_after_guessing_resets = []
    for otatable in OTAtables:
        new_r_start_index = len(table.R)
        new_r_end_index = len(otatable.R)
        temp_otatables = [otatable]
        #print(new_r_start_index, new_r_end_index)
        for i in range(new_r_start_index, new_r_end_index):
            resets_situtations = guess_resets_in_suffixes(otatable)
            #print(len(resets_situtations))
            new_tables = []
            for j in range(0, len(resets_situtations)):
                for temp_table in temp_otatables:
                    new_table = copy.deepcopy(temp_table)
                    temp_otatable = OTATable(new_table.S, new_table.R, new_table.E)
                    temp_otatable.R[i].suffixes_resets = resets_situtations[j]
                    new_table = copy.deepcopy(temp_otatable)
                    if True == fill(new_table.R[i],new_table.E,ota):
                        new_tables.append(new_table)
            temp_otatables = [tb for tb in new_tables]
            #print("a", len(temp_otatables))
        OTAtables_after_guessing_resets = OTAtables_after_guessing_resets + temp_otatables
        #print("b", len(OTAtables_after_guessing_resets))
    return OTAtables_after_guessing_resets

