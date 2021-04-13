import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df.plot()
plt.show()