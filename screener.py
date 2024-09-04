from io import StringIO
import pandas as pd
import yfinance as yf
import datetime as dt
import requests
from yahoo_fin import stock_info as si

# from si
def tickers_nifty50(include_company_data=False, headers={'User-agent': 'Mozilla/5.0'}):
    '''Downloads list of currently traded tickers on the NIFTY 50, India'''
    
    site = "https://finance.yahoo.com/quote/%5ENSEI/components?p=%5ENSEI"
    response = requests.get(site, headers=headers)
    html_str = response.text
    
    # Use StringIO to avoid FutureWarning
    table = pd.read_html(StringIO(html_str))[0]
    
    if include_company_data:
        return table
    
    nifty50 = sorted(table['Symbol'].tolist())
    return nifty50

# Get NIFTY 50 tickers
tickers = tickers_nifty50()

# Define start and end dates
start = dt.datetime.now() - dt.timedelta(days=365)
end = dt.datetime.now()

# Download NIFTY 50 data
nifty50_df = yf.download('^NSEI', start=start, end=end)
nifty50_df['Pct Change'] = nifty50_df['Adj Close'].pct_change()
nifty50_ret = (nifty50_df['Pct Change'] + 1).cumprod().iloc[-1]

# Create an empty DataFrame for final results
final_df = pd.DataFrame(columns=['Ticker', 'Latest_Price', 'Score', 'Ema50', 'Ema150', '52high', '52low', 'Recomm'])

# List to store returns compared to NIFTY 50
returnlist = []

# Loop through each ticker
for ticker in tickers:
    try:
        # Download stock data
        df = yf.download(ticker, start=start, end=end)
        df.to_csv(f'stockdata/{ticker}.csv')
        
        # Calculate stock return
        df['Pct Change'] = df['Adj Close'].pct_change()
        stock_return = (df['Pct Change'] + 1).cumprod().iloc[-1]
        
        # Calculate return compared to NIFTY 50
        return_comp = round((stock_return / nifty50_ret), 2)
        returnlist.append(return_comp)
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        returnlist.append(None)  # Add None if there's an error

# Create DataFrame of best performers
best_performers = pd.DataFrame(list(zip(tickers, returnlist)), columns=['Ticker', 'Returns Compared'])
best_performers['Score'] = best_performers['Returns Compared'].rank(pct=True) * 100

# Filter out tickers that are not best performers
filtered_best_performers = best_performers[best_performers['Score'] >= best_performers['Score'].quantile(0.6)]

# print(filtered_best_performers)

for ticker in filtered_best_performers['Ticker']:
    try:
        df = pd.read_csv(f'stockdata/{ticker}.csv',index_col=0)
        moving_avgs = [50,150]
        for ma in moving_avgs:
            df['Ema' + str(ma)] = round(df['Adj Close'].ewm(span=ma,adjust=True).mean(),2)
        ema_50 = df['Ema50'].iloc[-1]
        ema_150 = df['Ema150'].iloc[-1]
        latest_price = df['Adj Close'].iloc[-1]
        score = round(best_performers[best_performers['Ticker'] == ticker]['Score'].tolist()[0],2)
        low_52week = round(min(df['Low'][-(52*5):]), 2)
        high_52week = round(max(df['High'][-(52*5):]), 2)
        stock = yf.Ticker(ticker)
        peg_ratio = stock.get_info().get('pegRatio')
        recom = stock.get_info().get('recommendationKey')

        condition1 = latest_price>ema_50>ema_150
        condition2 = latest_price >= (1.3 * low_52week)
        condition3 = latest_price >= (0.75 * high_52week)
        condition4 = recom == 'buy'
        # if peg_ratio is not None:
        #     condition4 = 2 > peg_ratio
        # else:
        #     print(f"PEG RATIO NOT AVAILABLE FOR {ticker}")
        #     peg_ratio = NaN
        #     condition4 = True
            
        if condition1 and condition2 and condition3 and condition4:
            final_df.loc[len(final_df.index)] = [ticker, latest_price, score, ema_50, ema_150, high_52week, low_52week,recom]
    except Exception as e:
        print(f"{e} for {ticker}")

final_df.sort_values(by='Score',ascending=False, inplace=True)
print(final_df)