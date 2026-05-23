import streamlit as st
import os
from PIL import Image

st.set_page_config(page_title="Upload Receipt", page_icon="📸")

st.title("Step 1: Upload Receipt")

st.markdown("Please upload a `.jpg` or `.jpeg` image of your receipt.")

uploaded_file = st.file_uploader("Choose a receipt image", type=["jpg", "jpeg"])

if uploaded_file is not None:
    # Save the file temporarily
    os.makedirs(os.path.join("data", "temp"), exist_ok=True)
    temp_path = os.path.join("data", "temp", "current_receipt.jpg")
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.session_state["image_path"] = temp_path
    
    # If a new image is uploaded, clear old parsed data
    if "last_uploaded_name" not in st.session_state or st.session_state["last_uploaded_name"] != uploaded_file.name:
        st.session_state.pop("parsed_data", None)
        st.session_state.pop("claims", None)
        st.session_state["last_uploaded_name"] = uploaded_file.name
    
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    
    st.success("Receipt uploaded successfully! You can now proceed to Step 2.")
    if st.button("Proceed to Registration", type="primary"):
        st.switch_page("pages/2_Parsed_Results.py")
