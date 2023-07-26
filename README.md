# Matching Engine in python
The challenge is to build a matching engine handling mutliple instruments, limit and market orders with a max quantity of 1 000 000 and a maximal price granularity of 0.1. <br>
The engine currently does not handle expiring orders or cancel option.
## Setup the system
You can copy or clone the github repo in your current working directory to be able to run `from matching_engine import MatchingEngine`
The system takes as input a csv file with `;` as separators. <br>
The order should come with the following columns: 
- OrderID: `int` . The system will use those Ids to asses time priority.
- Symbol: `str` the instrument traded 
- Price: `float` 'MKT' for market order prices
- Side: `str` 'Buy' or 'Sell'
- OrderQuantity: `int` or `float` (but will be converted to int) number of "shares" 

To load and execute the engine on order stored in a csv file, run:
```
engine = MatchingEngine()
engine.load(path)
``` 
with `path` being the path toward your csv file or run.
To load and execute the engine on orders already loaded and stored in a pandas `DataFrame`, run:
```
engine = MatchingEngine()
engine.load(file_path=None,df=YourDataFrame)
```

The logs of the matching engine will appear in the console at runetime and will be saved in the current_working_directory under `Matching_Logs.csv`. The output are under the following format: 
- ActionType: action taken by the engine (acknowledge, reject and fill)
- OrderId
- Symbol
- Price
- Side
- OrderQuantity
- FillPrice: price at which the trade was filled
- FillQuantity: quantity traded
- Reason: the reason why the order was rejected from the engine if it got rejected

## How does it work?
The engine first loads the orders row by row and will perform a number of checks that will determine whether the order is loaded into a book or rejected. 
The checks are the following: 
  - The price is a number strictly positive or a string with value `MKT` for market orders. 
  - Round price to 1 decimal
  - The quantity is positive number and less than 1 000 000 units. 
  - OrderID are numerics and convert them to integers. 
  - Make sure the ticker is a string
  - Make sure there isn't any empty fields in the order.

If the order passes the requirements it is then acknowledge ("Ack"), otherwise rejected ("Reject"). <br>

From here the engine picks up the ticker in the row and check whether a book already exists for the given ticker. The row is then converted to an Order and added to the corresponding book.  At that moment the book makes the difference between market or limit orders, giving them 2 different routes. 
- **Market orders**: <br>
As they don't have a price the system will check whether liquidity is available from the other side of the book. If liquidity is found, the order is executed at the best price, eating the liquidity along the way. The liquidity is represented by price levels formed by a linked list of orders. The orders a linked following the time priority (their order id). <br>
The levels are positioned on a binary search tree. We will use the binary search tree to get the next best price level when the order dried the liquidity of the current level. If the liquidity is not big enough the remaining of the order that has not been filled is added to a market order level. This level wont be added to the search tree as it benefits from price information of the other side. The market order level has a better price/time priority over limit orders. <br>
  > ⚠️  If both sides of the book are only composed of market orders there will be no filling as we don't have any price information.

- **Limit orders**: <br>
For the limit orders the setup is slightly different. The first thing we check is whether there is already liquidity waiting only a price information to be matched, meaning market orders on both side of the book. If there is, the market orders waiting on both side of the book are matched at the price of our limit order, whithout impacting the limit order itself.<br>
Once one side of the book's market order has dried, we check whether there is still market liquidity for our limit order. If there isn't any market order we check whether there is any standing orders at a price good enough for us to process the order. Once again we go through the levels, and consume the liquidity one price at a time. If there isn't any interesting trade the order is logged in the book. If its price level doesn't exist yet it is created. 
When orders are crossing the "spread", the advantage is given to the longest lasting order without compromise (FIFO). <br> 
> *Example*: Two sell orders are standing at 100 and 110 for a quantity of a 100 each. A buy order comes in, the trader has no clue about the current trading level and is buying 200 papers at 150 per paper. The oldest sell order will be filled first at 150, benefiting from the misprice.

## Next Steps 
The improvements to be considered next: 
- Adding more type of orders (stop, stop_limit, etc)
- Develop the matching engine to use multithreading 
- Add cancel, expiration options on orders
- Add different matching algorithms (currently FIFO only)
