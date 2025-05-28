import streamlit as st
import pandas as pd
from url_prep import url_prep, get_model

# Set page configuration
st.set_page_config(
    page_title="Phishing URL Detector",
    page_icon="🔒",
    layout="wide"
)

# Load the model
model = get_model()

# Create a title and description
st.title("🛡️PhishShield:Phishing Website Detector")
st.markdown("""
This application helps detect phishing URLs using machine learning.
Just enter a URL in the text box below and click "Check".
""")

# Create input field
url = st.text_input("Enter URL to check:", "")

# Create prediction button
if st.button("Check"):
    if url:
        with st.spinner("Checking URL..."):
            try:
                # Get features from URL
                features, error = url_prep(url)
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    # Convert features to DataFrame
                    df = pd.DataFrame([features])
                    
                    # Make prediction
                    prediction = model.predict(df)[0]
                    probability = model.predict_proba(df)[0]
                    
                    # Display results
                    if prediction == 1:
                        st.error("⚠️ This URL is likely a phishing site!")
                        st.write(f"Confidence: {probability[1]*100:.2f}%")
                    else:
                        st.success("✅ This URL appears to be legitimate!")
                        st.write(f"Confidence: {probability[0]*100:.2f}%")
                    
                    # Display feature details
                    st.subheader("URL Analysis Details")
                    st.write(features)
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a URL to check")

# Add some styling
st.markdown("""
<style>
.stButton>button {
    background-color: #4CAF50;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Add footer
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit")
