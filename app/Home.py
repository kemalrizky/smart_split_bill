import streamlit as st

st.set_page_config(
    page_title="Smart Split Bill",
    page_icon="🧾",
    layout="centered"
)

st.title("Smart Split Bill 🧾")
st.markdown("""
Welcome to **Smart Split Bill**!

This application helps you and your friends split the bill effortlessly using advanced AI.
Simply upload your receipt, and we will automatically parse the items and charges.

### Steps:
1. **Upload**: Provide a clear photo of your receipt.
2. **Parsed Results & People**: Review the parsed items and add the people sharing the bill.
3. **Claiming**: Let everyone claim what they ordered.
4. **Result**: Get the final breakdown of what everyone owes, including proportionate charges.
""")

st.divider()

if st.button("✂️ Start Splitting Your Bill", type="primary", use_container_width=True):
    st.switch_page("pages/1_Upload.py")
