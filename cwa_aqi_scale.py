"""Native WeatherKit scale metadata for the unchanged Taiwan MOENV AQI.

The JSON layout is based on successful native Apple scale responses. Category
numbers, index bands, and labels follow Taiwan's official AQI definition; this
does not calculate AQI or substitute another country's pollutant thresholds.
"""

SCALE_NAME = 'TAIWAN_AQI'
_BANDS = ((0, 50), (51, 100), (101, 150), (151, 200), (201, 300), (301, 500))
_COLORS = ('#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8F3F97', '#7E0023')
_GLYPHS = ('aqi.low', 'aqi.medium', 'aqi.high', 'aqi.high', 'aqi.high', 'aqi.high')
_LABELS = {
    'en-US': ('Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous'),
    'zh-Hant-TW': ('良好', '普通', '對敏感族群不健康', '對所有族群不健康', '非常不健康', '危害'),
}


def taiwan_aqi_scale(language, scale):
    """Return the local scale for supported locales, or None for other requests."""
    if scale != SCALE_NAME or language not in _LABELS:
        return None
    traditional = language == 'zh-Hant-TW'
    labels = _LABELS[language]
    categories = [
        {'categoryNumber': i + 1, 'range': list(band), 'color': color,
         'categoryName': label, 'glyph': glyph}
        for i, (band, color, label, glyph) in enumerate(zip(_BANDS, _COLORS, labels, _GLYPHS))
    ]
    # Native scales use category midpoint stops, with both endpoint colors held.
    stops = [(0, _COLORS[0]), *zip((25, 75, 125, 175, 250, 350), _COLORS), (500, _COLORS[-1])]
    return {
        'name': SCALE_NAME, 'displayName': 'AQI (TW)', 'shortDisplayName': 'AQI',
        'longDisplayName': '臺灣(AQI)' if traditional else 'Taiwan AQI',
        'displayLabel': '空氣品質' if traditional else 'Air Quality',
        'language': 'zh-TW' if traditional else 'en', 'version': 1,
        'aqi': {'numerical': True, 'ascending': True, 'range': [0, 500],
                'categories': categories,
                'gradient': {'stops': [{'location': value, 'color': color} for value, color in stops]}},
    }
