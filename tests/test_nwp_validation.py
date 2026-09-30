from copy import deepcopy

from cwa_nwp import normalize_nwp


def product():
    initial=1789000000
    rows=[{'initialTime':initial,'forecastTime':initial+lead*3600,'leadHours':lead,'values':[value],'geometry':'g'}
          for lead,value in [(6,1),(12,3),(18,4),(24,6)]]
    return {'version':1,'generatedAt':initial+1000,'towns':[{'county':'test','town':'test'}],
            'fields':{'apcp':rows,'pressure':[]},'geometry':{'g':[{'distanceKm':1}]}},initial


def test_conflicting_cumulative_duplicates_do_not_create_rain_intervals():
    data,initial=product();duplicate=deepcopy(data['fields']['apcp'][1]);duplicate['values']=[2]
    data['fields']['apcp'].insert(2,duplicate)
    result=normalize_nwp(data,'test','test',initial+1000)
    assert [(row['end']-initial,row['amount']) for row in result['rainIntervals']]==[(21600,1),(86400,2)]


def test_identical_duplicates_preserve_valid_rain_intervals():
    data,initial=product();data['fields']['apcp'].insert(2,deepcopy(data['fields']['apcp'][1]))
    assert [row['amount'] for row in normalize_nwp(data,'test','test',initial+1000)['rainIntervals']]==[1,2,1,2]


def test_boolean_accumulation_is_not_numeric_rain():
    data,initial=product();data['fields']['apcp'][0]['values']=[True]
    assert [row['amount'] for row in normalize_nwp(data,'test','test',initial+1000)['rainIntervals']]==[1,2]
