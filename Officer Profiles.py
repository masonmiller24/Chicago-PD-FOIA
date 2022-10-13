#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas, numpy, timeit


# In[4]:


# Import
path = 'C:/Benchmark Analytics/Invisible Institute GitHub/unified data/fully-unified-data/'
new_rost = pandas.read_csv(path+'roster/roster__2018-03.csv')
old_rost = pandas.read_csv(path+'roster/roster_1936-2017_2017-04.csv')
prof = pandas.read_csv(path+'profiles/final-profiles.csv')
ref = pandas.read_csv(path+'profiles/officer-reference.csv')
unit_hist = pandas.read_csv(path+'unit-history/unit-history.csv')
unit_ref = pandas.read_csv(path+'data-dictionary/unit_reference.csv')
salary = pandas.read_csv(path+'salary/salary_2002-2017_2017-09.csv')
salary_filled = pandas.read_csv(path+'salary/salary-filled_2002-2017_2017-09.csv')
salary_ranks = pandas.read_csv(path+'salary/salary-ranks_2002-2017_2017-09.csv')
awards = pandas.read_csv(path+'awards/awards_1967-2017_2017-08.csv')


# ### Recode, merge (incomplete)

# In[ ]:


# Unit
unit_hist['unit_no'] = unit_hist['unit_no'].astype(str)
units = unit_hist.merge(unit_des, how='left', on='unit_no') # https://home.chicagopolice.org/about/police-districts/

# Roster and Profiles
rost = pandas.concat([new_rost, old_rost])
rost = rost.sort_values(by='uid')
rost.index=rost.uid
del rost['source'], rost['age']

# Filling missing roster information across different records of same officers (by UID)
rost = ros.groupby(ros.index).fillna(method='bfill')
rost = rost.groupby(rost.index).fillna(method='ffill')
# Drop duplicates
rost = rost.drop_duplicates()
roster = rost.drop_duplicates(subset='uid')
# Salary is a time-series - treat like activity features


# ### Officer information sorted by timestamp
# #### Links officers and their demographics to every activity record by which they appear in the data. Use officer UIDs and the ID of the respective activity (e.g., trr_id). No need to include characteristics of each activity yet.

# In[ ]:


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


# In[ ]:


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


# In[ ]:


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


# In[ ]:


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
#df.to_csv('C:/Benchmark Analytics/CPD output/officer_stories.csv')

