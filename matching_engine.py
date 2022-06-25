# -*- coding: utf-8 -*-
"""
Created on Sun Jun 19 23:29:13 2022

@author: Saint Georges
"""

import pandas as pd 
import csv 

class Order :
    """
    Order class 
    """
    def __init__(self, order_id:int, ticker:str, order_size:int, side:str, order_type:bool, price:float =None):
        """

        Parameters
        ----------
        order_id : int
            orderID also used to sort time priority.
        ticker : str
            instrument traded.
        order_size : int
            size of order.
        side : str
            Buy or Sell.
        order_type : bool
            Limit or market, 0 is market and 1 is limit.
        price : float, optional
            Price to trade at. The default is None.

        Returns
        -------
        None.

        """

        self.id = order_id
        self.ticker = ticker
        self.size = order_size  # Variable to track traded size (of matched orders)
        self.remaining = order_size
        self.side = side
        self.order_type = order_type
        self.price = price
    # components modified after adding order to a level queue or mkt level 
        self.next = None
        self.previous = None


class Level:
    """
    the price level in the orderbook
    We use double linked list and a binary search tree to process and match orders 
    """
    def __init__(self, order: Order):

        if(order.price =='MKT'):
            self.type = 'MKT'
        else:
            self.type='limit'
            self.price = order.price
        self.side = order.side
        self.total_quantity = order.remaining
        #queue reference 
        self.top: Order = order
        self.bottom: Order = order
        #Tree components
        self.parent: Level = None
        self.left: Level = None
        self.right: Level = None
        
    def add_to_queue(self, new_order: Order):
        """
        Add one order at the bottom of the queue

        Parameters
        ----------
        new_order : Order

        Returns
        -------
        None.

        """

        #updating queue
        if self.top is None:
            self.top  = new_order
        else :
            self.bottom.next = new_order # updating the position of previous bottom and new with respect to each others
        new_order.previous = self.bottom
        self.bottom = new_order #adding at bottom of queue
        #updating global quantity
        self.total_quantity += new_order.remaining

        
    def scalp_from_queue(self):
        """
        Take out of the top order from the queue (FIFO) and return it

        Returns
        -------
        taken_order : Order
            DESCRIPTION.

        """
        taken_order = self.top
        if(self.top):
            self.top = self.top.next
            if (self.top):
                self.top.previous = None #updating the position of the new top of queue
        if taken_order == self.bottom:
            self.bottom = None # if the queue is finished

        return taken_order
    
    def insert_in_queue(self,inserted_order):
        """
        Insert in queue in accordance with time priority of given order

        Parameters
        ----------
        inserted_order : Order

        Returns
        -------
        None.

        """

        if inserted_order.id>=self.bottom.id:
            self.add_to_queue(inserted_order)
        else : 
            order_after = self.bottom.previous
            while ((order_after is not None) & (order_after.id>inserted_order.id)):
                order_after = order_after.previous
            #inserting in the queue
            order_before = order_after.previous
            order_after.previous = inserted_order
            inserted_order.next = order_after
            inserted_order.previous = order_before
            order_before.next = inserted_order
        #updating the size of level
        self.total_quantity += inserted_order.remaining
        
class Direction :
    """One slice of the book regrouping all price levels for one direction of trade"""
    
    def __init__(self,side):

        self.root = None #initial price level
        self.side = side 
        self.global_quantity = 0 #total quantity on that side
        self.mkt_available: Level = None
        
    def log_order(self,logged_order):
        """
        Enters an order in the side of the book at a level if level exist, creates it otherwise.

        Parameters
        ----------
        logged_order : order

        Returns
        -------
        None.

        """

        if self.root is not None:
            #searching the levels in a binary search fashion 
            exploring = self.root
            while exploring is not None:
                if exploring.price < logged_order.price:
                    if(exploring.left is not None):
                        exploring = exploring.left
                    else: 
                        break
                elif exploring.price > logged_order.price:
                    if(exploring.right is not None):
                        exploring = exploring.right 
                    else: 
                        break
                else: 
                    exploring.insert_in_queue(logged_order) #we found the level so we just add the order to it
                    return
            #there was no corresponding level so we create one and link it to the tree
            if  logged_order.price> exploring.price:
                exploring.right = Level(logged_order)
                exploring.right.parent = exploring
            else :
                exploring.left = Level(logged_order)
                exploring.left.parent = exploring 
        else : 
            self.root = Level(logged_order)
        self.global_quantity += logged_order.size #adding quantity
        
    def extreme_finder(self, minmax: bool = True,starting_point: Level = None):
        """
        Function to return min or max of tree from strating point or root
        False : min 
        True : max

        Parameters
        ----------
        minmax : bool, optional
            The default is True.
        starting_point : Level, optional
            Starting point in the tree

        Returns
        -------
        current_lvl : TYPE
            DESCRIPTION.

        """
        #if starting point is specified we start from there
        if starting_point is not None: 
            current_lvl = starting_point
        else : 
            current_lvl= self.root
        if current_lvl is not None: 
            if(minmax):
                while current_lvl.right is not None:
                    current_lvl = current_lvl.right
            else:
                while current_lvl.left is not None:
                    current_lvl = current_lvl.left
            return current_lvl
        else : 
            return None
    
    def next_price(self,level,order_type):
        """
        Find the next best price and return corresponding level 
        Next price is the lowest price higher than current if we bought the liquidity away and the highest of lowest if we sold it
        Parameters
        ----------
        level : Level

        Returns
        -------
        Level

        """

        if order_type =='Buy':
            if(level is not None):
                if level.right is not None: #looking for minimum price in the leaf prices higher than current level
  
                    return self.extreme_finder(minmax=False, starting_point=level.right)
                else: 
                    #going up the tree to find the closest value to our right 
                    #we check that we are not in the case where we are somewhere on left node
                    potential_target = level.parent
                    cur = level 
                    if ( potential_target is not None):
                        while (potential_target is not None) :
                            if(cur == potential_target.right):
                                potential_target = potential_target.parent
                                cur = cur.parent
                            else :
                                break
                                
                        return potential_target
                    else:
                        return None
            else :

                return None
        else : 
            if(level is not None):
                if level.left: #looking for max price in the leaf prices lower than current level
                    return self.extreme_finder(minmax=True, starting_point=level.left)
                else :
                    #going up the tree to find the closest value to our left 
                    #we check that we are not in the case where we are somewhere on right node
                    potential_target = level.parent
                    cur = level 
                    if ( potential_target is not None):
                        while ((potential_target is not None) & (cur == potential_target.left)):
                               potential_target = potential_target.parent
                               cur = cur.parent
                        return potential_target
                    else:
                        return None

    def load_Mkt(self,order):
        """
        Add mkt order to market queue if existing, creates it otherwise

        Parameters
        ----------
        order : Order

        Returns
        -------
        None.

        """

        if(self.mkt_available is not None):
            self.mkt_available.insert_in_queue(order)
        else: 
            self.mkt_available = Level(order)
            
class FullBook: 
    """
    Full book for a ticker with both directions (bid and ask) 
    This is the level where match are made
    """

    
    def __init__(self, ticker):

        self.ticker = ticker
        self.bid = Direction(1)
        self.ask = Direction(0)
    
    def add_order_to_book(self, order_to_add):
        """
        Head function to add order to book 

        Parameters
        ----------
        order_to_add : order

        Returns
        -------
        None.

        """
        #check if the order is limit as all mkt orders are priced None

        if (order_to_add.price):
            self.run_limit_order(order_to_add)
        else:
            self.run_mkt_order(order_to_add)

    def run_limit_order(self, limit_order):
        """
        Will run the trade if liquidity is found (ask higher than order price or bid lower than order price)
        We will maintain the price priority when buy orders for example are posted higher than 2 current limit
        Parameters
        ----------
        limit_order : limit Order

        Returns
        -------
        None.

        """

        if limit_order.side == 'Buy':

            best_level = self.ask.extreme_finder(False) #finding the minimum price on the ask side
            mkt_orders = self.ask.mkt_available # checking that there is no mkt orders with high time priority (eventhough there shouldn't be)
            mkt_queue = self.bid.mkt_available #market order sitting there because no price 
            # as the limit order would be filled on the spot if a mkt is standing
            direction = self.bid
        else :
            best_level = self.bid.extreme_finder(True) #max price on bid side 
            mkt_orders = self.bid.mkt_available
            direction = self.ask
        if(mkt_orders is not None):
            if(mkt_queue is not None):
                self.spend_liquidity(mkt_orders,mkt_queue,limit_order.price)
            #trading market liquidity first 

            while ((limit_order.remaining>0)& (mkt_orders.top is not None)):
                self.trade(limit_order,mkt_orders)

        
        if best_level is not None : 
            if limit_order.side=='Buy':
                while((limit_order.remaining>0)& (best_level.price<=limit_order.price)):
                    self.trade(limit_order,best_level)
                    if(best_level.top is None) & (direction.next_price(best_level,limit_order.side) is not None):
                        #switching level 
                        best_level = direction.next_price(best_level,limit_order.side)
            else :        
                while((limit_order.remaining>0)& (best_level.price>=limit_order.price)):
                    self.trade(limit_order,best_level)
                    if(best_level.top is None) & (direction.next_price(best_level,limit_order.side) is not None):
                        #switching level 
                        best_level = direction.next_price(best_level,limit_order.side)
            if (limit_order.remaining>0):
                    #
                self.log_limit_order(limit_order)
        else : 
            self.log_limit_order(limit_order)
            #trade level and go up levels 
                
        
    def spend_liquidity(self,mkt_orders:Level, mkt_queue:Level, price:float):
        """
        Consume the mkt books once a price as come in 

        Parameters
        ----------
        mkt_order : Mkt order Level

        mkt_queue : Mkt order Level (other side of the book)

        price : price discovered by the arrived limit price


        Returns
        -------
        None.

        """

        while ((mkt_queue.top is not None) & (mkt_orders.top is not None)):
            if(mkt_orders.top.remaining>=mkt_queue.top.remaining):
                mkt_orders.top.remaining -= mkt_queue.top.remaining
                mkt_orders.total_quantity -= mkt_queue.top.remaining
                mkt_queue.total_quantity -= mkt_queue.top.remaining
                #respecting time priority in display
                if(mkt_orders.top.id > mkt_queue.top.id):
                    self.output(mkt_orders.top, mkt_queue.top,price,mkt_queue.top.remaining)
                else :
                    self.output(mkt_queue.top,mkt_orders.top,price, mkt_queue.top.remaining)
                mkt_queue.top.remaining = 0

            else:
                mkt_queue.top.remaining -= mkt_orders.top.remaining
                mkt_queue.total_quantity -= mkt_orders.top.remaining
                mkt_orders.total_quantity -= mkt_orders.top.remaining
                if(mkt_orders.top.id > mkt_queue.top.id):
                    self.output(mkt_orders.top, mkt_queue.top,price,mkt_orders.top.remaining)
                else :
                    self.output(mkt_queue.top,mkt_orders.top,price,mkt_orders.top.remaining)
                mkt_orders.top.remaining = 0
                
            if (mkt_orders.top.remaining ==0):
                mkt_orders.scalp_from_queue()
            if (mkt_queue.top.remaining ==0):
                mkt_queue.scalp_from_queue()

                    
        
    def trade(self, client_order: Order, level_order: Level):
        """
    Matching orders 

        Parameters
        ----------
        client_order : Order
            DESCRIPTION.
        level_order : Level
            DESCRIPTION.

        Returns
        -------
        level_order : TYPE
            DESCRIPTION.

        """

        if client_order.remaining<= level_order.top.remaining:
            level_order.top.remaining -= client_order.remaining
            level_order.total_quantity -= client_order.remaining
            
            if(client_order.order_type == 'MKT'):
                self.output(client_order, level_order.top, level_order.top.price, client_order.remaining)
            else:
                self.output(client_order, level_order.top, client_order.price, client_order.remaining)
            if (level_order.top.remaining==0):
                level_order.scalp_from_queue()
            client_order.remaining = 0
        else : 
            client_order.remaining -= level_order.top.remaining
            level_order.total_quantity -= level_order.top.remaining
            if (client_order.order_type=='MKT'):
                self.output(client_order, level_order.top, level_order.top.price, level_order.top.remaining)
            else :
                self.output(client_order, level_order.top, client_order.price, level_order.top.remaining)
            level_order.top.remaining = 0
            level_order.scalp_from_queue()

            
    def run_mkt_order(self, order:Order):
        """
        Get best price for mkt order and trade the liquidity, log the order in the mkt level 
        if no liauidity is available

        Parameters
        ----------
        order : MKT order

        Returns
        -------
        None.

        """

        if order.side == 'Buy':
            best_level = self.ask.extreme_finder(0) #finding the minimum price on the ask side
            mkt_orders = self.bid.mkt_available # checking that there is no mkt orders with high time priority (eventhough there shouldn't be)
            # as the limit order would be filled on the spot if a mkt is standing
            direction = self.ask
        else :
            best_level = self.bid.extreme_finder(1) #max price on bid side 
            mkt_orders = self.ask.mkt_available
            direction = self.bid

        if(mkt_orders is None):
            if (best_level is not None):
                #keep running while order is not fill completely and there is liquidity 
                while ((order.remaining > 0) & (best_level is not None)):
                    self.trade(order,best_level)

                    
                    if(best_level.top is None) & (direction.next_price(best_level,order.side) is not None):
                        #switching level 
                        best_level = direction.next_price(best_level,order.side)

                #we went through the whole liquidity of the other side 
                if(order.remaining>0):

                    self.log_mkt_order(order)
            else : 
                #no counterparty so we log

                self.log_mkt_order(order)
        else: 
             #no time priority so we log (meaning no counterparty too as liquidity should be dried up here)

             self.log_mkt_order(order)
             
    def log_mkt_order(self, mkt_order:Order):
        """
        log the mkt order in the corresponding mkt level

        Parameters
        ----------
        mkt_order : MKT Order
            DESCRIPTION.

        Returns
        -------
        None.

        """

        if mkt_order.side=="Buy":
            self.bid.load_Mkt(mkt_order)
        else:
            self.ask.load_Mkt(mkt_order)
            
    def log_limit_order(self,limit_order:Order):
        """
        log the limit in the corresponding direction and level  

        Parameters
        ----------
        limit_order : limit Order

        Returns
        -------
        None.

        """

        if limit_order.side=='Buy': 
            self.bid.log_order(limit_order)
        else :
            self.ask.log_order(limit_order)
        #self.run_book()
            
    def output(self, client_order:Order, book_side:Order, price:float, qty:int ):
        """
        Printing and logging trades in current working directory

        Parameters
        ----------
        client_order : Order
        book_side : Order

        Returns
        -------
        None.

        """
        if(book_side.price is not None):
            print('Fill',book_side.id, book_side.ticker,book_side.price, book_side.side, book_side.size, price, qty)
            row =['Fill',book_side.id, book_side.ticker,book_side.price, book_side.side, book_side.size, price, qty]
        else : 
            print('Fill',book_side.id, book_side.ticker,  'MKT', book_side.side,book_side.size, price, qty)
            row=['Fill',book_side.id, book_side.ticker,  'MKT', book_side.side,book_side.size, price, qty]       
        with open('Logs.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row) 
            f.close()
            
        if(client_order.price is not None):
            print('Fill',client_order.id, client_order.ticker, client_order.price, client_order.side, client_order.size, price, qty)
            row=['Fill',client_order.id, client_order.ticker, client_order.price, client_order.side, client_order.size, price, qty]
        else :
            print('Fill',client_order.id, client_order.ticker, 'MKT',client_order.side, client_order.size, price, qty)
            row=['Fill',client_order.id, client_order.ticker, 'MKT',client_order.side, client_order.size, price, qty]
        with open('Matching_Logs.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row) 
            f.close()
            
class MatchingEngine:
    """
    Matching engine dispatch the orders from csv to books and run books 
    """
    
    def __init__(self):
        self.books ={}
        fieldnames = ["ActionType","OrderId","Symbol","Price","Side","OrderQuantity","FillPrice","FillQuantity"]
        with open('Matching_Logs.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            f.close()
            
    def output(self,row,reject=False): 
        """
        Print and log the designated message in the current working directory

        Parameters
        ----------
        row : pandas Serie
            row of df input.
        reject : BOOL, optional
            Whether to reject to order or not. The default is False.

        Returns
        -------
        None.

        """
        
        with open('Matching_Logs.csv', 'a') as f:
            writer = csv.writer(f)
            if reject:
                print('Reject',row[0],row[1],row[2],row[3],row[4])
                writer.writerow(['Reject',row[0],row[1],row[2],row[3],row[4]])
            else:
                print('Ack',row[0],row[1],row[2],row[3],row[4])
                writer.writerow(['Ack',row[0],row[1],row[2],row[3],row[4]])
            f.close()
    
    def add_book(self, ticker):
        """
        Create a new book for the dedicated ticker
        
        Parameters
        ----------
        ticker : instrument ticker
        
        Returns
        -------
        None.

        """
        if (ticker not in self.books.keys()):
            self.books[ticker]=FullBook(ticker)
        else:
            print(ticker,"already found in books")
            
    def dispatcher(self,row):
        """
        Assign order to the right book and run it. 

        Parameters
        ----------
        row : pandas series 
            DESCRIPTION.

        Returns
        -------
        None.

        """

        if (row['Symbol'] not in self.books.keys()):
            self.add_book(row['Symbol'])
        #Creating order
        if(row['Price']=='MKT'):
            order = Order(row['OrderID'],row['Symbol'],row['OrderQuantity'],row['Side'],'MKT')
        else :
            order = Order(row['OrderID'],row['Symbol'],row['OrderQuantity'],row['Side'],'LIMIT',row['Price'])
        #adding order to book
        self.books[row['Symbol']].add_order_to_book(order)
        
    def clean_and_ack(self,row):
        """
        Clean the data received as input and create order if it passes the checks

        Parameters
        ----------
        row : row from input csv 

        Returns
        -------
        None.

        """
        rej = False
        if(row['Price']=='MKT'):
            if((row.isna().any())|(row['OrderQuantity']>1000000)):
                rej = True
        elif (row['Price'] is None) or (float(row['Price'])<=0):
            rej=True
        else: 
            if((row.isna().any())|(float(row['OrderQuantity'])>1000000)):
                rej=True
            else:
                row['Price'] = round(float(row['Price']),1)
        if (row['Side'] not in ['Buy','Sell']):
            rej = True
        row['OrderID'] = int(row['OrderID'][5:])
        self.output(row,rej)    
        if not rej :
            
            self.dispatcher(row)
            
    def load(self, file_path):
        """
        Loading csv as pandas df for easier cleaning
        for simplicity we assume that we can sort OrderId alphabetically to get time priority

        Parameters
        ----------
        file_path : String

        Returns
        -------
        None.

        """
        df = pd.read_csv(file_path,sep=';')
        print(df.shape)

        #df = df.values
        #adopting array format as we want to swipe our data only once, and not slice it through multiple angles 
        df.apply(lambda x:self.clean_and_ack(x), axis = 1)
        
