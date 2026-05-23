import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.core.calculator import validate_claims, calculate_subtotals, calculate_charges

st.set_page_config(page_title="Final Result", page_icon="💸")

st.title("Step 4: Final Result")

if "claims" not in st.session_state:
    st.warning("Please complete Step 3 first.")
    st.stop()

parsed_data = st.session_state["parsed_data"]
claims = st.session_state["claims"]

if not validate_claims(claims, parsed_data["items"]):
    st.error("Claims are invalid. Please return to Step 3 and fix them.")
    st.stop()
    
subtotals = calculate_subtotals(claims, parsed_data["items"])
charges = calculate_charges(parsed_data.get("charges", []), subtotals)

st.header("Splitted Bill 🧾")

total_app_sum = 0

for person in st.session_state["people"]:
    with st.container(border=True):
        st.subheader(person)
        
        subtotal = subtotals.get(person, 0)
        charge = charges.get(person, 0)
        total = subtotal + charge
        total_app_sum += total
        
        html_card = f"""
        <div style="background-color: #e9f0f7; padding: 20px; border-radius: 10px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #555555;">Subtotal:</span>
                <span style="color: #333333; font-weight: bold;">Rp {subtotal:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <span style="color: #555555;">Charges:</span>
                <span style="color: #333333; font-weight: bold;">Rp {charge:,.2f}</span>
            </div>
            <div style="border-top: 1px solid #d0deec; margin-bottom: 15px;"></div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #2c3e50; font-size: 1.2em; font-weight: bold;">Total to Pay:</span>
                <span style="color: #3d85c6; font-size: 1.4em; font-weight: bold;">Rp {total:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
        
st.divider()
st.subheader("Summary")
st.write(f"**Grand Total Calculated: Rp {total_app_sum:,.2f}**")
st.balloons()

st.divider()
if st.button("Start Over", type="primary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("Home.py")
