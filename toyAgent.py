from osbrain import run_agent
from osbrain import run_nameserver
from osbrain import Agent
import osbrain, random, time

#We will work with messages serialized in json
osbrain.config['SERIALIZER'] = 'json'

class Merchant(Agent):
    initial_budget = 100
    budget = 100
    product_values = {'H': 10, 'S': 20, 'T': 15}  # Subjective value of product types

    def on_init(self, preference='NR', risk_tolerance=0.5):
        super().on_init()
        self.preference = preference
        self.risk_tolerance = risk_tolerance  # Determines how much risk they're willing to take

    def on_new_msg(self, msg):
        product_type = msg['product type']
        price = msg['price']
        if self.budget < price:
            self.log_info("Not enough budget to buy")
        elif self.should_buy(product_type, price):
            self.budget -= price
            self.log_info(f"Buying {product_type} for {price}, remaining budget: {self.budget}")
        else:
            self.log_info("Not interested")

    def should_buy(self, product_type, price):
        # Define a reserve budget threshold (e.g., 20% of the initial budget)
        reserve_budget = 0.2 * self.initial_budget
        
        # If budget is below reserve, do not bid
        if self.budget < reserve_budget:
            return False
        
        if self.preference == 'R':  # Random preference
            return random.choice([True, False])
        elif self.preference == 'NR':  # Non-random preference
            value = self.product_values.get(product_type, 0)
            
            # Adjust the perceived value based on risk tolerance
            adjusted_value = value * (1 + self.risk_tolerance)
            
            # Affordability factor considers both price and remaining budget
            affordability_factor = self.budget / (3 * price)  # Scaled to prevent overspending
            
            # Dynamic risk adjustment: act more conservatively as the budget decreases
            dynamic_risk_adjustment = 1 - (self.initial_budget - self.budget) / self.initial_budget
            adjusted_value *= dynamic_risk_adjustment
            
            # Decide to buy if price is within the adjusted value and affordability factor
            return price <= adjusted_value * affordability_factor



#Simple class for an operator
class Operator(Agent):

    starting_price = 0
    bottom_price = 0
    fish_types = ['H', 'S', 'T']
    

    def on_init(self):
        # we create a communication of type publisher name "publish channel"
        self.num_fishes = 0
        self.num_merchants = 0
        self.merchants=[]
        self.bind('PUB', alias='publish_channel')
        


    def start_auction(self):
        for i in range(self.num_fishes):
            fish_type = random.choice(self.fish_types)  # Randomly select a fish type
            self.send_new_product(fish_type, i + 1)

    def send_new_product(self, fish_type, product_number):
        # we send a new product to the merchants subscribed
        price = self.starting_price
        self.send('publish_channel', {"product number": product_number, "product type": fish_type, "price": price})
        auction_round = 1
        # Start the auction process
        while price > self.bottom_price:
            # Simulate a time interval
            time.sleep(1)  # You can set the actual interval time here
            print("\n--------------------------- AUCTION ROUND: "+str(auction_round)+" ---------------------------\n")

            # Check if any merchant buys the fish
            if not self.check_for_purchase(price):
                price -= 2  # Decrease the price if no purchase
                self.send('publish_channel', {"product number": product_number, "product type": fish_type, "price": price})
            else:
                break
            auction_round += 1

    def check_for_purchase(self,price):
        '''# This function will check if any merchant buys the product.
        for merchant in self.merchants:
            # Send a message to the merchant to check if they should buy the product
            response = merchant.send('should_buy', {'price': price})
            if response:

                return True'''
        # No consigo que funcione esto aun
            
        return False



if __name__ == '__main__':

    fish_types = ['H', 'S', 'T']
    fish_type = random.choice(fish_types)
    num_merchants = 4
    num_fishes = 4
    starting_price = 50
    bottom_price = 2
    merchants = []
    # init
    ns = run_nameserver()
    Operator = run_agent('Operator', base=Operator)
    Operator.set_attr(num_fishes=num_fishes, num_merchants=num_merchants, starting_price=starting_price, bottom_price=bottom_price)


    # Run Merchant agents
    for i in range(num_merchants):
        
        choice = random.choice(['R', 'NR'])
        merchant = run_agent(f'Merchant_{i}', base=Merchant)
        money = random.randint(50, 200)
        merchant.set_attr(preference=choice, budget=money, initial_budget=money)
        merchants.append(merchant)

    for merchant in merchants:
        
        merchant.connect(Operator.addr('publish_channel'), handler='on_new_msg')

    
    
    # Log a message
    for alias in ns.agents():
        print(alias)

    Operator.start_auction()

    ns.shutdown()