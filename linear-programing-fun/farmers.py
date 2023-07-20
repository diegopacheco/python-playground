#
# Farmer’s problem
# With the planting season steadily approaching, 
# your farmer friend presents you with the following 
# problem. You have:
#  3 tons of potato seeds and 
#  4 tons of carrot seeds. To grow the crops 
#    efficiently, you also have 
#  5 tons of fertilizer, which has to be used 
#    when planting in a 
# 1:1 ratio (i.e. 1 kilogram of potatoes or 
#  carrots requires 
# 1 kilogram of fertilizer). The profit is 
#   1.2$/kg 1.2$/kg for potato seeds and 
# 1.7$/kg1.7$/kg for carrot seeds.
# How much potatoes and carrots should you 
# plant to maximize your profit this season?
# 
# python3.10 farmers.py
#
from pulp import *

# creating the model
model = LpProblem(sense=LpMaximize)

# variables - how much do we plant?
x_p = LpVariable(name="potatoes", lowBound=0)
x_c = LpVariable(name="carrots", lowBound=0)

# inequalities - don't use more than we have
model += x_p       <= 3000  # potatoes
model +=       x_c <= 4000  # carrots
model += x_p + x_c <= 5000  # fertilizer

# objective function - maximize the profit
model += x_p * 1.2 + x_c * 1.7

# solve (ignoring debug messages)
status = model.solve(PULP_CBC_CMD(msg=False))

print("potatoes:", x_p.value())
print("carrots:", x_c.value())
print("profit:", model.objective.value())