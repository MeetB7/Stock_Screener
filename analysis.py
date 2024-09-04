import yfinance as yf

import tradingview_ta as td

lnt = yf.Ticker("LT.NS")
print(lnt.get_info().get('pegRatio'))
print(lnt.get_info().get('recommendationKey'))

