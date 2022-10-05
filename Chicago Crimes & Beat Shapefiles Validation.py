#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas, numpy, requests, geopandas, pysal, matplotlib.pyplot as plt
from scipy import stats
from shapely.geometry import Polygon, mapping
from fitter import Fitter
import warnings
warnings.filterwarnings("ignore")
# pysal documentation: https://splot.readthedocs.io/en/latest/api.html#
# pysal edsa: https://pysal.org/esda/notebooks/spatialautocorrelation.html


# ### Load, recode, geocode Chicago Open Data Portal Crimes from 2001

# In[ ]:


df = pandas.read_csv('C:/Benchmark Analytics/Chicago Data Portal/Crimes_-_2001_to_Present.csv')
# Recode, clean
df['Primary Type'] = df['Primary Type'].str.lower()
df['Primary Type'] = df['Primary Type'].replace({'non - criminal':'non-criminal','non-criminal (subject specified)':'non-criminal',                                               'crim sexual assault':'criminal sexual assault'})
df['date'] = pandas.to_datetime(df['Date'])

# Dropping crimes w/missing geographies for now (<0.1% of total)
df = df.dropna(subset=['Location', 'Police Beats'], axis=0)
# Encode crimes as Geopandas point objects to later fit into police beat shapefiles
dfg = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude))


# In[15]:


# Plot (not necessary to run)
ax = rec.plot(color='white', edgecolor='black')
rec.plot(ax=ax, color='red', marker=".", markersize=1)


# In[ ]:


# Investigate how beat deprecation is treated in crimes file
odf = df[df['date']<=pandas.to_datetime('12/18/2012')]
ndf = df[df['date']>=pandas.to_datetime('12/18/2012')]
ob = odf['Beat'].dropna().astype(int).unique().tolist()
nb = odf['Beat'].dropna().astype(int).unique().tolist()
ob == nb #True
# Exact same set of beats before & after beat deprecation on 12/18/2012 - file must have placed old crimes in current beats


# ### Chicago PD beat shapefiles

# In[ ]:


# Beats Shapefiles - Current
new_beats = geopandas.read_file('C:/Benchmark Analytics/Chicago Data Portal/beats/Boundaries - Police Beats (current).zip')
new_beats = new_beats.sort_values(by=['district', 'sector', 'beat', 'beat_num']) # remove leading zero on district number
new_beats['beat_num'] = new_beats['beat_num'].str.lstrip('0')

# Beats Shapefiles - effective 12/19/2012 (apparently 2 diff web pages for the same beat shapefiles)
#val_path = 'C:/Benchmark Analytics/Chicago Data Portal/beats/Boundaries - Police Beats (effective 12_19_2012).zip'
#val_beats = geopandas.read_file(val_path)
#val_df = val_beats == beats 
#val_df.sum() == len(val_df)
#val_df.sum() == len(beats)
# files are exactly the same


# In[ ]:


# Beats Shapefiles - deprecated 12/18/2012: https://data.cityofchicago.org/Public-Safety/Boundaries-Police-Beats-deprecated-on-12-18-2012-/kd6k-pxkv
old_path = 'C:/Benchmark Analytics/Chicago Data Portal/beats/PoliceBeats.zip'
old_beats = geopandas.read_file(old_path)
old_beats.columns = old_beats.columns.str.lower()
old_beats = old_beats.sort_values(by=['district', 'sector', 'beat', 'beat_num']) # remove leading zero on district number
old_beats['beat_num'] = old_beats['beat_num'].str.lstrip('0')

# Reproject old beats to lat/lon coordinates
old_beats = old_beats.to_crs(epsg=4326)

# Combine beat files
old_beats['version'] = 'old'
new_beats['version'] = 'new'
beats = pandas.concat([new_beats, old_beats])
beats = beats.sort_values(by=['beat_num'])
beats = beats.reset_index(drop=True)
beats['coors'] = beats['geometry'].apply(mapping)


# In[56]:


# New and deprecated beats
old_beat_ids = old_beats.beat_num.values.tolist()
new_beat_ids = new_beats.beat_num.values.tolist()
new_beat_ids == old_beat_ids # False
new_ids = [x for x in new_beat_ids if x not in old_beat_ids]
deprecated_ids = [x for x in old_beat_ids if x not in new_beat_ids]
print('new beats: ', new_ids)
print('deprecated beats: ', deprecated_ids)


# In[ ]:


# Compare old and new beats to see whether the polygon changed
beat_compare = pandas.DataFrame(index=beats.beat_num.unique())
for b in beats.beat_num.unique().tolist():
    comparison = beats[beats['beat_num']==b]
    try:
        beat_compare.loc[b, 'match'] = comparison.geometry.values.tolist()[0] == comparison.geometry.values.tolist()[1]
    except:
        print(b)
# Polygon comparison evaluates to False even though all dimensions are the same - geopandas quirk (?) - using current beats for now
#beats[beats.beat_num.isin(new_ids)].plot()
#new_beats.plot()
#old_beats.plot()


# ### Histogram - Total Crimes by Beat

# In[135]:


ctb.hist(column='total', bins=50)


# ### Choropleth - Crimes by Beat

# In[62]:


bc.plot('total', legend=True)

