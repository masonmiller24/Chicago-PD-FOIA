#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas, numpy, sys, geopandas
from scipy import stats
import warnings
warnings.filterwarnings("ignore")


# ### Load, recode, geocode Chicago Open Data Portal Crimes from 2001

# In[3]:


df = pandas.read_csv('C:/Benchmark Analytics/Chicago Data Portal/Crimes_-_2001_to_Present.csv')
# Recode, clean
df['Primary Type'] = df['Primary Type'].str.lower()
df['Primary Type'] = df['Primary Type'].replace({'non - criminal':'non-criminal','non-criminal (subject specified)':'non-criminal',                                               'crim sexual assault':'criminal sexual assault'})
df['date'] = pandas.to_datetime(df['Date'])

# Dropping crimes w/missing geographies for now (<0.1% of total)
df = df.dropna(subset=['Location', 'Police Beats'], axis=0)
# Encode crimes as Geopandas point objects to later fit into police beat shapefiles
dfg = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude))


# ### Chicago PD beat shapefiles

# In[4]:


# Beats Shapefiles - Current
new_beats = geopandas.read_file('C:/Benchmark Analytics/Chicago Data Portal/beats/Boundaries - Police Beats (current).zip')
new_beats = new_beats.sort_values(by=['district', 'sector', 'beat', 'beat_num']) # remove leading zero on district number
new_beats['beat_num'] = new_beats['beat_num'].str.lstrip('0')


# ### Crime "Primary Type" Distribution by Beat

# In[5]:


# Crime "Primary Type" distribution by Beat
beat_crimes = []
for beat_num in df.Beat.unique():
    d = df[df['Beat']==beat_num]
    beat_crimes.append({beat_num: d['Primary Type'].value_counts()})
# Dataframe
ctb = pandas.DataFrame(beat_crimes[0]).transpose()
for item in beat_crimes[1:]:
    ctb = pandas.concat([ctb, pandas.DataFrame(item).transpose()])
ctb['total'] = ctb.sum(axis=1)
ctb.index = ctb.index.astype(str)


# In[29]:


# Merge crimes & types to beat shapefiles
bc = new_beats.merge(ctb, left_on='beat_num', right_index=True)
bc = bc.fillna(0)
bc = bc.reset_index(drop=True)


# ### Fitting Distributions on Crime Counts across Beats

# In[40]:


f.fitted_param # Grabbing fitted params of mielke dist.


# ### Function - percentile of Chicago crime in beat during given window

# In[25]:


def crime_compare(crime_df, date_start, date_end, time_start=None, time_end=None, crime_type='total'):
    """crime_df: df of crimes from Chicago Open Data Portal disaggregated by CPD beat
       start: first day of comparison window, format: 1/1/2015
       end: last day of comparison window, format 12/31/2015
       
       returns: mielke distribution (to allow skew) fit on crimes by beat.
       query the crime percentile of any beat with miekle.cdf(crime_count_in_beat)""" 
    if time_start:
        start = pandas.to_datetime(date_start + ' ' + time_start)
    else:
        start = pandas.to_datetime(date_start)
    if time_end:
        end = pandas.to_datetime(date_end + ' ' + time_end)
    else:
        end = pandas.to_datetime(date_end)
        
    # Filter crimes to specified window
    df = crime_df[crime_df['date']>=pandas.to_datetime(start)]
    df = df[df['date']<=pandas.to_datetime(end)]
    bybeat = df.Beat.value_counts().to_dict()
    vals = numpy.array(list(bybeat.values()))
    
    # Fit mielke distribution
    mielke_params = stats.mielke.fit(vals)
    mielke = stats.mielke(mielke_params[0],mielke_params[1],mielke_params[2],mielke_params[3])
    print('mean: ', mielke.mean(), 'median: ', mielke.median())
    return(mielke)


# In[35]:


crime_dist = crime_compare(df, date_start='1/1/2000', date_end='12/31/2020')
crime_dist.cdf(bc.loc[269, 'total'])


# ### Severity Comparison across Beats - 22 Ordinal Rankings from Universal Crime Reporting (UCR) manual

# In[ ]:


# Descriptions of crimes by Primary Type
df[df['Primary Type']=='ritualism'].Description.value_counts()


# In[129]:


# 22 ordinal severity rankings of crime, adapted from Universal Crime Reporting guidelines
sev = pandas.read_excel('C:/Benchmark Analytics/Chicago Data Portal/crimes_severity.xlsx')
sev['severity'] = 22 - sev['severity']
df = df.merge(sev, how='left', left_on='Primary Type', right_on='primary type')


# In[140]:


df.hist(column='severity', bins=22)


# In[ ]:


# CDFs of crime severity distribution, overall and for each beat
hist, bins = numpy.histogram(df['severity'], bins=22)
pdf = hist / sum(hist)
cdf = numpy.cumsum(pdf)
cdfs = {}
for beat in df.Beat.unique():
    d = df[df['Beat']==beat]
    hist, bins = numpy.histogram(d['severity'], bins=22)
    pdf = hist / sum(hist)
    cdf = numpy.cumsum(pdf)
    cdfs[beat] = cdf


# In[132]:


# Plot crime severity CDFs of all beats
plt.plot(cdf, color='black')
for key in cdfs.keys():
    plt.plot(cdfs[key])


# In[ ]:


# Kolmogorov-Smirnov tests, comparing crime severity dist. in each beat to overall dist.
ks = {}
for key in cdfs.keys():
    ks[key] = stats.kstest(cdf, cdfs[key])
ks # Results, ctrl+F "pvalue=0.0" to find rejected beats


# In[139]:


# KS test significant for 6 beats
reject_beats = [134, 310, 1214, 1653, 1652, 1655]
plt.plot(cdf, color='black') # overall dist. in black
for beat in reject_beats:
    plt.plot(cdfs[beat])
# Increase ordinality of crime severity to potentially reject more beats
# How to encode divergent crime severity distributions as features?

