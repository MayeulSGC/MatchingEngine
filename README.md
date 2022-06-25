# MatchingEngine
## Matching Engine challenge in python
The challenge is to build a matching engine handling mutliple instruments, limit and market orders with a max quantity of 1 000 000 and a maximal price granularity of 0.1. <br>
The engine currently does not handle expiring orders or cancel option.
### Setup the system
You can copy or clone the github repo in your current working directory to be able to run `from matching_engine import MatchingEngine`
The system takes as input a csv file with `;` as separators. <br>
The order should come with the following columns: 
- OrderID: in the form Order1, Order2, ... OrderN. The system will use those Ids to asses time priority.
- Symbol: the instrument traded
- Price: numeric, 'MKT' for market order prices
- Side: 'Buy' or 'Sell'
- OrderQuantity: number of "shares" 

To run the system you need to instanciate the MatchingEngine class and then run `MatchingEngine.load(path)` with `path` being the path toward your csv file. 

The log of the matching engine will appear in the console and will be saved in the current_working_directory under `Matching_Logs.csv`. The output are under the following format: 
- ActionType: action taken by the engine (acknowledge, reject and fill)
- OrderId
- Symbol
- Price
- Side
- OrderQuantity
- FillPrice: price at which the trade was filled
- FillQuantity: quantity traded

### How it works
The engine first loads the data and will check that no element in the row is missing. It will check the quantity and whether the price is either 'MKT' or a positive float. If the granularity is lower than 0.1 the price is rounded. If the order passes the requirements it is then acknowledge, otherwise rejected. <br>
From here the engine picks up the ticker in the row and check whether a book already exists for the given ticker. The row is then converted to an Order and added to the corresponding book.  
At that moment the book makes the difference between market or limit orders, giving them 2 different routes. 
- Market orders: as they don't have a price the system will check whether liquidity is available from the other side of the book. If the other side is only composed of market orders there will be no filling as we don't have any price information. If liquidity is found, the order is executed at the best price, eating the liquidity along the way. The liquidity is represented by price levels formed by a linked list of orders. The orders a linked following the time priority (their order id). The levels are positioned on a binary search tree. We will use the binary search tree to get the next best price level when the order dried the liquidity of the current level. If the liquidity is not big enough the remaining of the order that has not been filled is added to a market order level. This level wont be added to the search tree as it benefits from price information of the other side. The market order level has a better price/time priority over limit orders. 
- Limit orders: for the limit orders the setup is slightly different. The first thing we check is whether there is already liquidity waiting only a price information to be matched, meaning market orders on both side of the book. if there is the liquidity is dried up at the price of the limit order, whithout impact the limit order itself. Once one side of the book's market order has dried, we check whether their is still market liquidity for our limit order. If there isn't any market order we check whether there is any standing orders at a price good enough for us to process the order. Once again we go through the levels, and consume the liquidity one price at a time. If there isn't any interesting trade the order is logged in the book. If its price level doesn't exist yet it is created. 
When orders are crossing the "spread", the advantage is given to the longest lasting order without compromise. <br> 
  - Example: Two sell orders are standing at 100 and 110 for a quantity of a 100 each. A buy order comes in, the trader has no clue about the current trading level and is buying 200 papers at 150 per paper. The sell orders, standing there first will benefit from the misprice and be filled at 150. 

### Next Steps 
The improvements to be considered next: 
- adding more type of orders (stop, stop_limit, etc)
- develop the matching engine to use multithreading 
- add cancel, expiration options on orders
- add different matching algorithms 
