request_data(historyData = [(symbol('SPY'), '1 day', '50 D'), (symbol('AAPL'), '1 day', '50 D')])
# symbol, unit_interval, time_interval
# S seconds, D days, W weeks
print(data[symbol('SPY')].hist('1 day'))
