import streamlit as st
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core.parser import parse_receipt

st.set_page_config(page_title="Parsed Results", page_icon="🔍")

st.title("Step 2: Parsed Results & Registration")

if "image_path" not in st.session_state or not os.path.exists(st.session_state["image_path"]):
    st.warning("Please upload an image in Step 1 first.")
    st.stop()
    
if "parsed_data" not in st.session_state:
    with st.spinner("Parsing receipt using AI... This might take a few seconds."):
        parsed = parse_receipt(st.session_state["image_path"])
        if "error" in parsed:
            st.error(f"Failed to parse receipt: {parsed['error']}")
            st.stop()
        
        # Filter zero-price items out
        parsed["items"] = [i for i in parsed.get("items", []) if i.get("price", 0) > 0]
        st.session_state["parsed_data"] = parsed
        
parsed = st.session_state["parsed_data"]

st.subheader("Extracted Items")
st.dataframe(parsed.get("items", []), use_container_width=True)

st.subheader("Extracted Charges")
st.dataframe(parsed.get("charges", []), use_container_width=True)

st.divider()

st.subheader("Register People")
st.markdown("Add the names of everyone sharing this bill.")

if "people" not in st.session_state:
    st.session_state["people"] = []

# Form to add a new person
with st.form("add_person_form", clear_on_submit=True):
    new_person = st.text_input("Name")
    add_btn = st.form_submit_button("Add Person")
    if add_btn and new_person.strip():
        if new_person.strip() not in st.session_state["people"]:
            st.session_state["people"].append(new_person.strip())
            st.rerun()
        else:
            st.warning("Person already exists!")

st.write("### Registered People:")
for i, person in enumerate(st.session_state["people"]):
    col1, col2 = st.columns([0.8, 0.2])
    col1.write(f"{i+1}. {person}")
    if col2.button("Remove", key=f"del_{i}"):
        st.session_state["people"].remove(person)
        if "claims" in st.session_state and person in st.session_state["claims"]:
            del st.session_state["claims"][person]
        st.rerun()
            
st.divider()

if st.button("Proceed to Claim Items", type="primary"):
    if len(st.session_state["people"]) >= 1:
        st.switch_page("pages/3_Claiming.py")
    else:
        st.error("You must register at least 1 person before proceeding.")
