brokerList = {}
pairList = []
posList = []
priceList = {}
pred = \
    {  # Prediction dict
        'AUD/JPY': None,
        'AUD/NZD': None,
        'AUD/USD': None,
        'CAD/JPY': None,
        'CHF/JPY': None,
        'EUR/CHF': None,
        'EUR/GBP': None,
        'EUR/JPY': None,
        'EUR/USD': None,
        'GBP/JPY': None,
        'GBP/USD': None,
        'NZD/USD': None,
        'USD/CAD': None,
        'USD/CHF': None,
        'USD/JPY': None
    }

dct = {'backtest': {}}
dct['backtest'] = \
    {
        'EUR_USD': 'EUR/USD',
        'USD_JPY': 'USD/JPY'
    }

dctInv = {'backtest': {}}
dctInv['backtest'] = \
    {
        'EUR/USD': 'EUR_USD',
        'USD/JPY': 'USD_JPY'
    }

dctPred = \
    {
        'AUDJPY': 'AUD/JPY',
        'AUDNZD': 'AUD/NZD',
        'AUDUSD': 'AUD/USD',
        'CADJPY': 'CAD/JPY',
        'CHFJPY': 'CHF/JPY',
        'EURCHF': 'EUR/CHF',
        'EURGBP': 'EUR/GBP',
        'EURJPY': 'EUR/JPY',
        'EURUSD': 'EUR/USD',
        'GBPJPY': 'GBP/JPY',
        'GBPUSD': 'GBP/USD',
        'NZDUSD': 'NZD/USD',
        'USDCAD': 'USD/CAD',
        'USDCHF': 'USD/CHF',
        'USDJPY': 'USD/JPY'
    }
dctPredInv = \
    {
        'AUD/JPY': 'AUDJPY',
        'AUD/NZD': 'AUDNZD',
        'AUD/USD': 'AUDUSD',
        'CAD/JPY': 'CADJPY',
        'CHF/JPY': 'CHFJPY',
        'EUR/CHF': 'EURCHF',
        'EUR/GBP': 'EURGBP',
        'EUR/JPY': 'EURJPY',
        'EUR/USD': 'EURUSD',
        'GBP/JPY': 'GBPJPY',
        'GBP/USD': 'GBPUSD',
        'NZD/USD': 'NZDUSD',
        'USD/CAD': 'USDCAD',
        'USD/CHF': 'USDCHF',
        'USD/JPY': 'USDJPY'
    }
