import os
import joblib
import pandas as pd

def test_model():
    print("Testing model loading...")
    model_path = "model/phishing.pkl"
    
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return False
    
    try:
        print("Trying to load model with joblib...")
        model = joblib.load(model_path)
        print("Model loaded successfully!")
        
        # Example dummy data (adjust keys to match your model's features)
        dummy_data = {
            'length_url': 30,
            'length_hostname': 10,
            'nb_dots': 2,
            'nb_hyphens': 1,
            'nb_at': 0,
            'nb_qm': 0,
            'nb_and': 1,
            'nb_eq': 0,
            'nb_tilde': 0,
            'nb_slash': 2,
            'nb_colon': 1,
            'nb_semicolumn': 0,
            'nb_www': 1,
            'nb_com': 1,
            'nb_dslash': 1,
            'http_in_path': 1,
            'https_token': 1,
            'ratio_digits_url': 0.1,
            'tld_in_path': 0,
            'nb_subdomains': 1,
            'shortening_service': 0,
            'path_extension': 0,
            'ip': 0,
            'nb_redirection': 0,
            'nb_hyperlinks': 5,
            'nb_extCSS': 1,
            'external_favicon': 0,
            'links_in_tags': 5,
            'ratio_intMedia': 0.8,
            'iframe': 0,
            'empty_title': 0,
            'domain_in_title': 1,
            'domain_with_copyright': 1,
            'whois_registered_domain': 1
        }
        
        # Convert to DataFrame
        df = pd.DataFrame([dummy_data])
        
        # Make prediction
        prediction = model.predict(df)
        print(f"Prediction result: {prediction[0]}")
        
        return True
        
    except Exception as e:
        print(f"Error loading or predicting with model: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_model()