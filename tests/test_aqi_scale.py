import pytest

from cwa_aqi_scale import taiwan_aqi_scale
from cwa_aqi import normalize_aqi
from cwa_model import epoch


def test_taiwan_scale_matches_native_schema_and_official_categories():
    scale = taiwan_aqi_scale('zh-Hant-TW', 'TAIWAN_AQI')
    assert scale['name'] == 'TAIWAN_AQI'
    assert scale['language'] == 'zh-TW' and scale['version'] == 1
    assert scale['longDisplayName'] == '臺灣(AQI)' and scale['displayLabel'] == '空氣品質'
    aqi = scale['aqi']
    assert aqi['numerical'] is True and aqi['ascending'] is True and aqi['range'] == [0, 500]
    assert [c['range'] for c in aqi['categories']] == [[0, 50], [51, 100], [101, 150], [151, 200], [201, 300], [301, 500]]
    assert [c['categoryNumber'] for c in aqi['categories']] == [1, 2, 3, 4, 5, 6]
    assert [c['categoryName'] for c in aqi['categories']] == ['良好', '普通', '對敏感族群不健康', '對所有族群不健康', '非常不健康', '危害']
    assert [c['color'] for c in aqi['categories']] == ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8F3F97', '#7E0023']
    assert [s['location'] for s in aqi['gradient']['stops']] == [0, 25, 75, 125, 175, 250, 350, 500]


@pytest.mark.parametrize('index,category', [(0, 1), (50, 1), (51, 2), (100, 2), (101, 3), (150, 3), (151, 4), (200, 4), (201, 5), (300, 5), (301, 6), (500, 6)])
def test_scale_bands_agree_with_unchanged_moenv_observation(index, category):
    now = epoch('2026-09-30T20:00:00+08:00')
    data = {'data': {'aqi': [{'aqi': str(index), 'latitude': '25.09', 'longitude': '121.56', 'publishtime': '2026/09/30 20:00:00'}]}}
    observed = normalize_aqi(data, 25.09, 121.56, now)
    scale = taiwan_aqi_scale('en-US', observed['scale'])
    native_category = next(c['categoryNumber'] for c in scale['aqi']['categories'] if c['range'][0] <= observed['index'] <= c['range'][1])
    assert observed['index'] == index and observed['categoryIndex'] == native_category == category


def test_scale_language_and_unrelated_identifiers():
    scale = taiwan_aqi_scale('en-US', 'TAIWAN_AQI')
    assert scale['language'] == 'en' and scale['longDisplayName'] == 'Taiwan AQI'
    assert scale['aqi']['categories'][2]['categoryName'] == 'Unhealthy for Sensitive Groups'
    assert taiwan_aqi_scale('zh-Hant-TW', 'EPA_NowCast.2604') is None
    assert taiwan_aqi_scale('zh-Hant-TW', 'TAIWAN_AQI/extra') is None
    assert taiwan_aqi_scale('unsupported', 'TAIWAN_AQI') is None
