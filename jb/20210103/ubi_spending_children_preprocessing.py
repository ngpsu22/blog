# -*- coding: utf-8 -*-
"""Percent - How much should a child get?

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MXNFC_ClLnHFupipXG618P39Tunavn7C
    graphs removed
    

"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import microdf as mdf

person = pd.read_csv('https://github.com/MaxGhenis/datarepo/raw/master/pppub20.csv.gz',
                     usecols=['MARSUPWT', 'SPM_ID', 'SPM_POVTHRESHOLD',
                                  'SPM_RESOURCES','A_AGE', 'TAX_INC', 'SPM_WEIGHT', 'SPM_NUMPER'])

# Lower column headers and adapt weights
person.columns = person.columns.str.lower()
person['person_weight'] = person.marsupwt / 100
person.spm_weight /= 100

# Determine age demographic
person['child'] = person.a_age < 18
person['adult'] = person.a_age > 17

# calculate population statistics
adult_pop = (person.adult * person.weight).sum()
child_pop = (person.child * person.weight).sum()
pop = child_pop + adult_pop

# Create SPMU dataframe
spmu = person.groupby(['spm_id', 'spm_weight', 'spm_povthreshold', 'spm_resources', 'spm_numper'])[['child', 'adult', 'tax_inc']].sum()

total_taxable_income = (spmu.tax_inc * spmu.spm_weight).sum()

def poverty_gap(df, resources, threshold, weight):
    gaps = np.maximum(df[threshold] - df[resources], 0)
    return (gaps * df[weight]).sum()


def ubi(funding_billions=0, child_percent=0):
  """ Calculate the poverty rate among the total US population by:
  
  -passing a total level of funding for a UBI proposal (billions USD),
  -passing a percent of the benefit recieved by a child and the benefit
  recieved by an adult
  AND
  taking into account that funding will be raise by a flat tax leveled on each households
  taxable income """

  child_percent /= 100

  funding = funding_billions * 1e9

  target_persons = person.copy(deep=True)

  # i think this is % funding, not % benefit
  adult_ubi = ((1 - child_percent) * funding) / adult_pop
  child_ubi = (child_percent * funding) / child_pop

  tax_rate = funding / total_taxable_income

  spmu['new_tax'] = tax_rate * spmu.tax_inc
  spmu['spm_ubi'] = (spmu.child * child_ubi) + (spmu.adult * adult_ubi)

  spmu['new_spm_resources'] = spmu.spm_resources + spm_ubi - spmu.new_tax
  spmu['new_spm_resources_pp'] = spmu.new_spm_resources / spmu.numper

  # Calculate poverty gap
  poverty_gap = poverty_gap(spmu, 'new_spm_resources', 'spm_povthreshold', 'spmweight')

  # Merge person and spmu dataframes

  target_persons = person.merge(spmu, left_on='spm_id')

  total_poor = (target_persons.poor * target_persons.person_weight).sum()
  poverty_rate = (total_poor / pop * 100)

  # Calculate Gini
  gini = mdf.gini(target_persons, 'new_spm_resources_pp', w='person_weight')

  # Percent winners
  target_persons['better_off'] = (target_persons.new_spm_resources > target_persons.spm_resources)
  total_better_off = (target_persons.better_off * target_persons.weight).sum()
  percent_better_off = total_better_off / pop

  return pd.Series([poverty_rate, gini, poverty_gap, percent_better_off, adult_ubi, child_ubi])

# create a dataframe with all possible combinations of funding levels and
summary = mdf.cartesian_product({'funding_billions': np.arange(0,3_001,50),
                                 'percent': np.arange(0, 101, 1)})

def ubi_row(row):  
    return ubi(row.funding_billions, row.percent)
summary[['poverty_rate', 'gini', 'poverty_gap', 'percent_better_off', 'adult_ubi', 'child_ubi']] = summary.apply(ubi_row, axis=1)

"""## Save `summary` to CSV"""

summary['monthly_child_ubi'] =summary['child_ubi'].apply(lambda x: int(round(x/12,0)))
summary['monthly_adult_ubi'] =summary['adult_ubi'].apply(lambda x: int(round(x/12,0)))
summary.to_csv("children_share_ubi_spending_summary.csv.gz",compression='gzip')

"""## `optimal_[whatever concept]` `dataframe`s for `ubi()` """

# drop rows where funding level is 0
optimal_poverty = summary.sort_values('poverty_gap').drop_duplicates('funding_billions', keep='first')
optimal_poverty = optimal_poverty.drop(
    optimal_poverty[optimal_poverty.funding_billions==0].index
    ) 

optimal_inequality = summary.sort_values('gini').drop_duplicates('funding_billions', keep='first')
optimal_inequality = optimal_inequality.drop(
    optimal_inequality[optimal_inequality.funding_billions==0].index
    ) 

optimal_winners = summary.sort_values('percent_better_off').drop_duplicates('funding_billions', keep='last')
optimal_winners = optimal_winners.drop(
    optimal_winners[optimal_winners.funding_billions==0].index
    )