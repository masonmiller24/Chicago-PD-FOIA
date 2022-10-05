#!/usr/bin/env python
# coding: utf-8

# In[5]:


import pandas, numpy, timeit


# In[21]:


# Validation - DONT RUN
trr15 = main[main['datetime']>=pandas.to_datetime('1/1/2015')]
trr15 = trr15[trr15['datetime']<=pandas.to_datetime('12/31/2015')]
len(trr15) #5,373 vs. 6,455 per dashboard: https://home.chicagopolice.org/statistics-data/data-dashboards/use-of-force-dashboard/
# dashboard breaks down by location, subject demos, so we can narrow down which are missing from FOIA data


# ### Run starting here

# In[10]:


# TRR import
path = 'C:/Benchmark Analytics/Invisible Institute GitHub/unified data/fully-unified-data/'
ar = pandas.read_csv(path+'/TRR/TRR-actions-responses_2004-2016_2016-09.csv')
chg = pandas.read_csv(path+'/TRR/TRR-charges_2004-2016_2016-09.csv')
main = pandas.read_csv(path+'/TRR/TRR-main_2004-2016_2016-09.csv')
off = pandas.read_csv(path+'/TRR/TRR-officers_2004-2016_2016-09.csv')
stat = pandas.read_csv(path+'/TRR/TRR-statuses_2004-2016_2016-09.csv')
subj = pandas.read_csv(path+'/TRR/TRR-subjects_2004-2016_2016-09.csv') # event_ids == data portal's "incidents"
subjw = pandas.read_csv(path+'/TRR/TRR-subject-weapons_2004-2016_2016-09.csv')
wd = pandas.read_csv(path+'/TRR/TRR-weapon-discharges_2004-2016_2016-09.csv')


# In[11]:


# Recode, merge
main['date_time'] = main['trr_date'] + ' ' + main['trr_time']
main['datetime'] = pandas.to_datetime(main['date_time'])
notify_recode = {'Yes':1, numpy.nan:0}
main['notify_OEMC'], main['notify_district_sergeant'], main['notify_OP_command'], main['notify_DET_division'] = main['notify_OEMC'].replace(notify_recode), main['notify_district_sergeant'].replace(notify_recode), main['notify_OP_command'].replace(notify_recode), main['notify_DET_division'].replace(notify_recode)
main['address'] = main['block'] + ' ' + main['direction'].str[0] + ' ' + main['street']

# Subjects
subjw = subjw.fillna('')
subjw['weapon'] = subjw['weapon_type'] + ' ' + subjw['firearm_caliber'] + subjw['weapon_description']
subj = subj.merge(subjw, how='left', on='trr_id')
subj = subj.rename(columns={'race':'subj_race','gender':'subj_gender','birth_year':'subj_birth_year','armed':'subj_armed',                           'injured':'subj_injured','alleged_injury':'subj_alleged_injury','age':'subj_age','weapon':                            'subj_weapon','trr_date':'event_date'})
subj['subj_birth_year'] = subj['subj_birth_year'].replace({numpy.float64(1901.0):numpy.nan})
main = main.merge(subj, how='left', on='trr_id')

# Officers
del off['row_id']
off = off.rename(columns={'injured':'off_injured'})
off.unit_detail = off.unit_detail.fillna(0)
off['unit.detail'] = off['unit_detail'].astype(int)
off['unit.detail'] = off['unit'].astype(str) +  '.' + off['unit_detail'].astype(str)
off['unit.detail'] = off['unit.detail'].str.rstrip('.0')
off = off[['trr_id','off_injured','unit.detail','assigned_beat','UID']]
main = main.merge(off, how='left', on='trr_id')

# Actions-Responses
ar['action'] = ar['action'].replace({'OTHER (SPECIFY)':numpy.nan})
ar.action.fillna(ar['member_action'], inplace=True)
ar['other_description'] = ar['other_description'].fillna('')
ar['action'] = ar['action'] + ' ' + ar['other_description']
ar['action'] = ar['action'].str.rstrip(' ')
del ar['resistance_level'], ar['member_action'], ar['other_description']
main = main.merge(ar, how='left',on='trr_id')

# Charges
chg = chg.rename(columns={'subject_no':'chg_subject_no','description':'charge_description'})
main = main.merge(chg[['trr_id','statute','charge_description','chg_subject_no']])

# 
del main['sr_no_x'],main['se_no_x'], main['date_time'], main['trr_time'], main['sr_no_y'], main['se_no_y'],main['action_category']

cols = main.columns.tolist()
cols.insert(0, cols.pop(cols.index('event_id')))
main['action_sub_category'] = main['action_sub_category'].fillna(0)
main = main.sort_values(by=['event_id', 'trr_id', 'action_sub_category'])
trr = main[cols]
trr = trr.reset_index(drop=True)
#trr.to_csv('C:/Benchmark Analytics/my output/TRRs merged.csv')


# In[260]:


# Weapons-Discharges
#main = main.merge(wd, how='left', on='trr_id')
wd = pandas.read_csv(path+'/TRR/TRR-weapon-discharges_2004-2016_2016-09.csv')
wd['weapon_type'] = wd['weapon_type'].replace({'OTHER (SPECIFY)':numpy.nan})
wd.weapon_type.fillna(wd['weapon_type_description'], inplace=True)
wd['NaN'] = numpy.nan
for i in wd.index:
    if wd.loc[i, 'weapon_type'] == wd.loc[i, 'weapon_type_description']:
        wd.loc[i, 'weapon_type_description'] = numpy.nan
    wd.loc[i, 'NaN'] = wd.loc[[i]].isna().sum().sum()


# In[1]:


# Investigate usefulness of Weapons-Discharges
#wd[wd['NaN']!=17]['NaN'].value_counts()
#wd[wd['NaN']==16]


# ### Experimenting with TRRs as Python classes

# In[556]:


class event:
    """Event in which one or more officers used force (UoF) against one or more subjects."""
    
    def __init__(self, event_id, datetime):
        self.datetime = datetime
        self.event_id = event_id
        self.event_location = None#self.location()
        self.event_TRR = None
        
    def details(self):
        print(f'Event #{self.event_id}')
        print(f'Date/Time: {self.datetime}')
        if self.event_location != None:
            print('Location: ')
            print(self.event_location.details())
        
    class location:
        """Location of event, common across any and all TRRs (defined below)"""
        def __init__(self, beat, address, setting, in_or_out, light, weather):
            self.beat = beat
            self.address = address
            self.setting = setting
            self.indoor = self.whether_indoor(in_or_out)
            self.light = light
            self.weather = weather
            
        def details(self):
            print(f'Beat: {self.beat}') 
            print(f'Address: {self.address}')
            print(f'Setting: {self.in_or_out}, {self.setting.lower()} ')
            print(f'Light: {self.light.lower()}')
            print(f'Weather: {self.weather.lower()}')
            
        def whether_indoor(self, in_or_out):
            self.in_or_out = in_or_out
            if in_or_out == 'Outdoor':
                return(0)
            elif in_or_out == 'Indoor':
                return(1)
    class TRR:
        """A tactical response report (TRR) is a single instance of a use-of-force pairing between an officer and a subject.
       May be multiple TRRs in a single event, hence TRR class is nested under event class."""
    
        def __init__(self, trr_id, subject, officer):
            self.trr_id = trr_id
            self.subject = subject
            self.officer = officer
            
        class subject:
            def __init__(self, subject_id, gender, race, age, actions, charges):
                self.gender = gender
                self.race = race
                self.age = age
                self.actions = []
                self.charges = []
            
            def add_actions(self, action):
                for a in actions:
                    self.actions.append(a)
                    
            def add_charges(self, charges):
                for c in charges:
                    self.charges.append(c)
                
        class officer:
            def __init__(self, uid, assigned_beat, unit_detail, actions):
                self.uid = uid
                self.unit_detail = unit_detail
                self.assigned_beat = assigned_beat
                self.actions = []


# In[557]:


e2 = event(event_id = trr.loc[8, 'event_id'], datetime=trr.loc[8, 'datetime'])
e2.event_location = e2.location(beat=trr.loc[0, 'beat'], address=trr.loc[0, 'address'], setting=trr.loc[0, 'location_recode'],                 in_or_out=trr.loc[0, 'indoor_or_outdoor'], light=trr.loc[0, 'lighting_condition'],                 weather=trr.loc[0, 'weather_condition'])
e2.event_TRR = e2.TRR(trr.loc[8, 'trr_id'], trr.loc[8, 'subject_ID'], trr.loc[8, 'UID'])
e2.event_TRR.subject(trr.loc[8, 'subject_ID'])


# ### Officer time-series code was written on invalid data - only keeping in case it helps

# In[4]:


# Merges
# Complaints
complaints = compl.merge(off_compl, how='left', on='complaint_no') # 41,893 w/o uid but w/ dates/location
# Unit
unit['unit_no'] = unit['unit_no'].astype(str)
units = unit.merge(unit_des, how='left', on='unit_no') # https://home.chicagopolice.org/about/police-districts/
# Roster and Profiles
ros = pandas.concat([prof, roster])
ros = ros.sort_values(by='uid')
ros.index=ros.uid
del ros['source'], ros['age']
rost = ros.groupby(ros.index).fillna(method='bfill')
rost = rost.groupby(rost.index).fillna(method='ffill')
rost = rost.drop_duplicates()
roster = rost.drop_duplicates(subset='uid')
# Salary is a time-series


# In[126]:


def officer_ts(uid, roster=roster, units=unit, complaints=complaints, trr=trr, salary=salary, awards=awards):
    """Creates long df containing all of 1 officer's records"""
    df = officer_roster(uid, roster=roster)
    df = add_activity(uid, df, units, 'unit')
    df = add_activity(uid, df, salary, 'salary')
    df = add_activity(uid, df, complaints, 'complaint')
    df = add_activity(uid, df, awards, 'award')
    df = add_activity(uid, df, trr, 'trr')
    df = df.sort_values(by='date')
    return(df)


# In[127]:


def officer_roster(uid, roster=roster):
    r = roster[roster['uid']==uid].reset_index(drop=True)
    officer = {}
    officer['uid'] = r.loc[0, 'uid']
    officer['name'] = r.loc[0, 'first_name'].lower() + ' ' + r.loc[0, 'last_name'].lower()
    officer['gender'] = r.loc[0, 'gender']
    officer['race'] = r.loc[0, 'race']
    officer['date'] = r.loc[0, 'appointment_date']
    if officer['date'] != numpy.nan:
        officer['date'] = pandas.to_datetime(officer['date'])
    officer['birthyear'] = r.loc[0, 'birthyear']
    officer['activity'] = 'appointed'
    officer['value'] = numpy.nan
    df = pandas.DataFrame(officer, index=[0])
    return(df)


# In[128]:


def add_activity(uid, officer, activity_df, activity_type='unit'):
    """"Input: dataframe from officer_roster
        Output: dataframe with activities from df added"""
    activity_map = {'unit':'joined unit','salary':'salary','complaint':'complaint','award':'award',                   'trr':'use of force'}
    date_map = {'unit':'start_date','salary':'year','complaint':'incident_datetime',                'award':'award_request_date', 'trr':'date'}
    value_map = {'unit':'unit_no','salary':'salary','complaint':'complaint_no','award':'award_type',                 'trr':'trr_id'}
    
    officer_activities = activity_df[activity_df['uid']==uid].reset_index(drop=True)
    if activity_type=='award':
        officer_activities = officer_activities[officer_activities['current_status']=='FINAL'].reset_index(drop=True)
    l = len(officer_activities)
    rows = len(officer)
    for r in range(1, l+1):
        new_row = officer.loc[0].to_dict()
        new_row['activity'] = activity_map[activity_type]
        new_row['value'] = officer_activities.loc[r-1][value_map[activity_type]]
        if activity_type == 'salary':
            new_row['date'] = pandas.to_datetime('1/1/' + str(officer_activities.loc[r-1].year))
        #elif activity_type == 'complaint':
        #    new_row['date'] = officer_activities.loc[r-1, date_map[activity_type]]
        else:
            new_row['date'] = pandas.to_datetime(officer_activities.loc[r-1, date_map[activity_type]])
        officer.loc[rows-1+r] = new_row
    return(officer)


# In[208]:


def build_units(unit_df, unit_no):
    """Units composed of officers and dates of their membership to unit"""
    unit = unit_df[unit_df['unit_no']==unit_no]
    start = unit['start_date'].sort_values(ascending=True).head(1).values[0]
    end = unit['end_date'].sort_values(ascending=False).head(1).values[0]
    
units[units['unit_no']=='7']


# In[ ]:


# 1/17/2004 - 4/12/2016 - only 10,579 TRR records
# 1/1/2015 - 8/18/2022 - 36,296 TRR records
# https://informationportal.igchicago.org/tactical-response-reports-overview/


# In[132]:


# officer_TS for all officers - export
start = timeit.timeit()
dfs = []
count = 0
for uid in roster.uid.unique().tolist():
    temp = officer_ts(uid)
    dfs.append(temp)
    count+=1
    if count % 1000 == 0:
        print(count)
df = pandas.concat(dfs)
df = df.reset_index(drop=True)
end = timeit.timeit()
print(end - start)
df.to_csv('C:/Benchmark Analytics/CPD output/officer_stories.csv')


# In[168]:


complaints['incident_datetime'] = pandas.to_datetime(complaints['incident_datetime'])
c15 = complaints[complaints['incident_datetime']>=pandas.to_datetime('1/1/2015')]
c15 = c15[c15['incident_datetime']<=pandas.to_datetime('12/31/2015')]


# In[188]:


# trr: block, street_direction, street_name
# complaint: street_no, street_name, city
complaints.head(1)


# In[211]:


cc = complaints['complaint_category'].value_counts().to_dict()
for key in cc:
    print(key)


# In[221]:


roster.to_csv('C:/Benchmark Analytics/my output/roster_profiles_cleaned.csv')


# In[224]:


complaints.finding.value_counts() / len(complaints)

