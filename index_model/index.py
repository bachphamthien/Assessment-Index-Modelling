import pandas as pd,numpy as np
from datetime import datetime as dt
import os

cwd = os.getcwd()

class IndexModel:
    def __init__(self):
        # Get data
        self.data = pd.read_csv(cwd + '\\data_sources\\stock_prices.csv',index_col='Date') # Load in data
        self.data.index = pd.to_datetime(data.index,format="%d/%m/%Y")
        self.trading_calendar = 'B' # Monday to Friday
        self.index_levels = None # Placeholder

    def calc_index_level(self, start_date:dt.date, end_date:dt.date) -> None:
        ## Getting date range from start_date to end_date
        self.trading_dates = pd.date_range(start_date,end_date,freq=self.trading_calendar)
        self.trading_dates.freq = None
        self.trading_dates = list(self.trading_dates)
        ## Combine with dates with data
        self.trading_dates.extend(list(self.data.index))
        self.trading_dates = list(set(self.trading_dates))
        self.trading_dates.sort()
        
        ## In case there are missing data for any date, forward fill
        self.data = self.data.reindex(self.trading_dates).fillna(method='ffill')
        
        ## Getting the rebalancing dates
        self.data['day'] = self.data.index
        self.data['month'] = self.data.index.map(lambda x:x.month)
        self.reba_dates = list(self.data.iloc[1:][~self.data['month'].iloc[1:].eq(self.data['month'].shift(1).dropna())].index)
        
        ## Getting the selection dates
        self.selection_dates = self.data['day'].shift(1).loc[self.reba_dates].to_dict()
        
        ## Calculating perf for each month
        self.coll = []
        self.data = self.data[[col for col in self.data.columns if 'stock' in col.lower()]]
        for i,d in enumerate(self.reba_dates):
            ### Getting the top 3 prices, all stocks have the same nb of shares
            wts = self.data.copy().loc[self.selection_dates[d]].sort_values(ascending=False).iloc[:3]
            wts.loc[:] = np.array([0.5,0.25,0.25])
            if i != len(self.reba_dates) - 1: # On rebalancing dates other than the last one
                perf = self.data.copy().loc[d:self.reba_dates[i+1],wts.index]
            else: # On the last rebalancing date
                perf = self.data.copy().loc[d:,wts.index]
            perf = (perf/perf.iloc[0]*wts).apply(sum,axis=1) # Rebase cumulated perf to 1, multiply with weights and sum 
            
            if i != 0: # If it's not the first rebalancing date, multiply the perf with the last value of the index
                perf = pd.concat([self.coll[-1],perf*self.coll[-1].iloc[-1]],axis=0) # Concat to add current month's perf
                perf = perf[~perf.index.duplicated(keep='first')] # Dropping the duplicate rebalancing date
            self.coll.append(perf) # If it's the first rebalancing date, only append it
        self.index_levels = self.coll[-1]*100 # Index is the last element of self.coll
        return self.index_levels

    def export_values(self, file_name: str) -> None:
        if not self.index_levels is None:
            self.index_levels.to_csv(cwd + u'\\{0}.csv'.format(file_name))
        else:
            print("Please run the calc_index_level method first")
