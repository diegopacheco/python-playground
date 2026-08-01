import pandas as pd
import streamlit as st

st.title("Python Essentials Streamlit")
st.write("A small interactive data app.")

name = st.text_input("Your name", "alice")
st.write(f"Hello, {name}")

count = st.slider("How many rows", min_value=3, max_value=20, value=5)

data = pd.DataFrame(
    {
        "n": list(range(1, count + 1)),
        "square": [i * i for i in range(1, count + 1)],
        "cube": [i ** 3 for i in range(1, count + 1)],
    }
)

st.subheader("Table")
st.dataframe(data)

st.subheader("Chart")
st.line_chart(data.set_index("n"))

if st.button("Show sum"):
    st.success(f"sum of squares = {int(data['square'].sum())}")
