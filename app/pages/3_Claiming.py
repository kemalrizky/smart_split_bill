import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.core.calculator import validate_claims

st.set_page_config(page_title="Claim Items", page_icon="📝")

st.title("Step 3: Claim Items")

if "parsed_data" not in st.session_state or "items" not in st.session_state["parsed_data"]:
    st.warning("Please complete Step 2 first.")
    st.stop()
    
if "people" not in st.session_state or not st.session_state["people"]:
    st.warning("Please add people in Step 2 first.")
    st.stop()
    
if "claims" not in st.session_state:
    st.session_state["claims"] = {person: {} for person in st.session_state["people"]}
    
# Sync claims with current people list
for person in st.session_state["people"]:
    if person not in st.session_state["claims"]:
        st.session_state["claims"][person] = {}
        
people_to_remove = [p for p in st.session_state["claims"] if p not in st.session_state["people"]]
for p in people_to_remove:
    del st.session_state["claims"][p]

parsed_items = st.session_state["parsed_data"]["items"]

# Calculate remaining quantities
claimed_totals = {}
for person, p_claims in st.session_state["claims"].items():
    for item_name, qty in p_claims.items():
        claimed_totals[item_name] = claimed_totals.get(item_name, 0) + qty

st.markdown("Each person can claim items below.")

for person in st.session_state["people"]:
    with st.expander(f"Claims for {person}", expanded=True):
        st.write(f"**{person}'s Items:**")
        
        claims = st.session_state["claims"][person]
        
        # Display existing claims
        items_to_delete = []
        for item_name, qty in claims.items():
            col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
            col1.write(item_name)
            col2.write(f"Qty: {qty}")
            if col3.button("❌", key=f"del_{person}_{item_name}"):
                items_to_delete.append(item_name)
                
        for item_name in items_to_delete:
            del st.session_state["claims"][person][item_name]
            st.rerun()
            
        st.divider()
        
        # Determine available items for new claims
        available_items_for_dropdown = []
        for it in parsed_items:
            rem = it["quantity"] - claimed_totals.get(it["name"], 0)
            if rem > 0:
                available_items_for_dropdown.append(it["name"])
                
        if not available_items_for_dropdown:
            st.info("No items left to claim.")
        else:
            col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
            selected_item = col1.selectbox("Select Item", options=available_items_for_dropdown, key=f"sel_{person}")
            
            # Find item price and remaining quantity
            item_price = 0
            max_qty = 1
            for it in parsed_items:
                if it["name"] == selected_item:
                    item_price = it["price"] / it["quantity"]
                    max_qty = it["quantity"] - claimed_totals.get(it["name"], 0)
                    break
            
            col2.write("Unit Price")
            col2.write(f"Rp {item_price:,.0f}")
            
            qty = col3.number_input("Qty", min_value=1, max_value=max_qty, step=1, key=f"qty_{person}")
            
            if st.button("Add Item", key=f"btn_{person}"):
                if selected_item in st.session_state["claims"][person]:
                    st.session_state["claims"][person][selected_item] += qty
                else:
                    st.session_state["claims"][person][selected_item] = qty
                st.rerun()

st.divider()

if st.button("Calculate Split Bill", type="primary", use_container_width=True):
    is_valid = validate_claims(st.session_state["claims"], parsed_items)
    if is_valid:
        st.switch_page("pages/4_Result.py")
    else:
        st.error("Invalid claims detected (e.g. claiming more than available). Please adjust your claims.")
