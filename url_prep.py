from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup
import random
import joblib

user_agents_list = [
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
]

def _nb_subdomains(url):
    parsed_url = urlparse(url)
    subdomain_number = parsed_url.netloc.split('.')[:-2]
    return len(subdomain_number)

def _path_extension(url):
    extensions_to_check = [".exe", ".html", ".pdf", ".txt"]
    parsed_url = urlparse(url)
    path = parsed_url.path
    for ext in extensions_to_check:
        if path.endswith(ext):
            return 1
    return 0

def _nb_redirection(url):
    max_redirects = 10
    current_url = url
    redirect_count = 0
    while redirect_count < max_redirects:
        try:
            response = requests.head(current_url, allow_redirects=False)
            if 300 <= response.status_code < 400:
                redirect_url = response.headers['Location']
                if not redirect_url.startswith("http"):
                    redirect_url = current_url + redirect_url
                current_url = redirect_url
                redirect_count += 1
            else:
                break
        except requests.exceptions.RequestException:
            break
    return redirect_count

def _req_feats(url):
    data = {
        "nb_hyperlinks": 0,
        "nb_extCSS": 0,
        "external_favicon": 0,
        "links_in_tags": 0,
        "ratio_intMedia": 0,
        "iframe": 0,
        "empty_title": 0,
        "domain_in_title": 0,
        "domain_with_copyright": 0,
        "whois_registered_domain": 0,
    }

    error = ""
    try:
        headers_list = [
            {
                "User-Agent": random.choice(user_agents_list),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            },
            {
                "User-Agent": random.choice(user_agents_list),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "close"
            }
        ]

        response = None
        for headers in headers_list:
            try:
                response = requests.get(url, headers=headers, timeout=5, verify=False, allow_redirects=True)
                if response.status_code == 200:
                    break
            except requests.exceptions.SSLError:
                url_http = url.replace('https://', 'http://', 1)
                response = requests.get(url_http, headers=headers, timeout=5, verify=False, allow_redirects=True)
                if response.status_code == 200:
                    break
            except Exception:
                continue

        if response and response.status_code == 200:
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            hyperlinks = soup.find_all('a')
            external_css_links = [link.get("href") for link in soup.find_all("link", rel="stylesheet")]
            favicon_link = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            img_tags = soup.find_all('img')
            video_tags = soup.find_all('video')
            total_media_count = len(img_tags) + len(video_tags)
            img_count = len(img_tags)
            iframe_tags = soup.find_all('iframe')
            title_tag = soup.find('title')
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            try:
                import pythonwhois
                domain_info = pythonwhois.get_whois(domain)
                if domain_info:
                    data["whois_registered_domain"] = 1 if domain_info.get('status') else 0
                else:
                    data["whois_registered_domain"] = 0
            except ImportError:
                try:
                    import whois
                    domain_info = whois.whois(domain)
                    if hasattr(domain_info, 'status') and domain_info.status is not None:
                        data["whois_registered_domain"] = 0
                    else:
                        data["whois_registered_domain"] = 1
                except Exception:
                    data["whois_registered_domain"] = 0

            if total_media_count > 0:
                media_ratio = (img_count / total_media_count) * 100
            else:
                media_ratio = 0

            data["external_favicon"] = 1 if favicon_link else 0
            data["iframe"] = 1 if iframe_tags else 0

            if title_tag:
                data["empty_title"] = 0
                title_text = title_tag.text.strip()
                data["domain_in_title"] = 1 if domain in title_text else 0
            else:
                data["empty_title"] = 1
                data["domain_in_title"] = 0

            data["domain_with_copyright"] = 1 if " " in domain else 0
            data["nb_hyperlinks"] = len(hyperlinks)
            data["links_in_tags"] = data["nb_hyperlinks"]
            data["nb_extCSS"] = len(external_css_links)
            data["ratio_intMedia"] = media_ratio

        else:
            data.update({
                "nb_hyperlinks": 0,
                "nb_extCSS": 0,
                "external_favicon": 0,
                "links_in_tags": 0,
                "ratio_intMedia": 0,
                "iframe": 0,
                "empty_title": 1,
                "domain_in_title": 0,
                "domain_with_copyright": 0,
                "whois_registered_domain": 0
            })
            
            data["nb_redirection"] = 1  
            data["shortening_service"] = 1  
            data["ip"] = 1  
            
            error = "Phishing"

    except Exception as e:
        data.update({
            "nb_hyperlinks": 0,
            "nb_extCSS": 0,
            "external_favicon": 0,
            "links_in_tags": 0,
            "ratio_intMedia": 0,
            "iframe": 0,
            "empty_title": 1,
            "domain_in_title": 0,
            "domain_with_copyright": 0,
            "whois_registered_domain": 0
        })
        
        data["nb_redirection"] = 1
        data["shortening_service"] = 1
        data["ip"] = 1
        
        error = "Phishing"

    return data, error

def url_prep(url):
    data = {}
    url_tld_list = [".com", ".net", ".org", ".gov", ".edu", ".mil", ".int", ".co.uk", ".fr", ".de", ".jp"]
    shortening_services = {"bit.ly": r"bit\.ly/[\w\d]+", "t.co": r"t\.co/[\w\d]+"}
    ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    data["length_url"] = len(url)
    second_part = url.split("://")[1]
    hostname = second_part.split("/")[0]
    data["length_hostname"] = len(hostname)
    data["nb_dots"] = url.count(".")
    data["nb_hyphens"] = url.count("-")
    data["nb_at"] = url.count("@")
    data["nb_qm"] = url.count("?")
    data["nb_and"] = url.count("&")
    data["nb_eq"] = url.count("=")
    data["nb_tilde"] = url.count("~")
    data["nb_slash"] = url.count("/")
    data["nb_colon"] = url.count(":")
    data["nb_semicolumn"] = url.count(";")
    data["nb_www"] = url.count("www")
    data["nb_com"] = url.count("com")
    data["nb_dslash"] = url.count("//")

    http_number = url.count("http")
    https_number = url.count("https")
    data["http_in_path"] = http_number - https_number
    data["https_token"] = https_number

    num_count = 0
    char_count = 0
    url_split = url.split("://", 1)[1]
    for char in url_split:
        if char.isnumeric():
            num_count += 1
        elif char.isalpha():
            char_count += 1
    if char_count == 0:
        char_count += 1

    data["ratio_digits_url"] = num_count / char_count

    for tld in url_tld_list:
        if tld in url:
            data["tld_in_path"] = 1
            break
        else:
            data["tld_in_path"] = 0

    data["nb_subdomains"] = _nb_subdomains(url)

    for service, pattern in shortening_services.items():
        if re.search(pattern, url):
            data["shortening_service"] = 1
            break
        else:
            data["shortening_service"] = 0

    data["path_extension"] = _path_extension(url)
    data["ip"] = 1 if re.search(ip_pattern, url) else 0
    data["nb_redirection"] = _nb_redirection(url)

    results, error = _req_feats(url)
    data.update(results)
    return data, error

import warnings
import sys
import os
from sklearn.exceptions import DataConversionWarning, DataDimensionalityWarning

warnings.filterwarnings("ignore", category=DataConversionWarning)
warnings.filterwarnings("ignore", category=DataDimensionalityWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

model = None

def load_model():
    global model
    model_path = "model/phishing.pkl"
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        print("Please ensure the model file exists in the 'model' directory.")
        sys.exit(1)
    try:
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.tree import DecisionTreeClassifier
        original_fit = DecisionTreeClassifier.fit
        def patched_fit(self, *args, **kwargs):
            if not hasattr(self, 'monotonic_cst'):
                self.monotonic_cst = None
            return original_fit(self, *args, **kwargs)
        DecisionTreeClassifier.fit = patched_fit
        model = joblib.load(model_path)
        print("Model loaded successfully with joblib")
        if hasattr(model, 'estimators_'):
            for estimator in model.estimators_:
                if not hasattr(estimator, 'monotonic_cst'):
                    estimator.monotonic_cst = None
        return
    except Exception as e:
        print(f"Joblib load failed: {str(e)}")
        import traceback
        traceback.print_exc()
    try:
        import pickle
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        print("Model loaded successfully with pickle")
        if hasattr(model, 'estimators_'):
            for estimator in model.estimators_:
                if not hasattr(estimator, 'monotonic_cst'):
                    estimator.monotonic_cst = None
        return
    except Exception as e:
        print(f"Pickle load failed: {str(e)}")
        import traceback
        traceback.print_exc()
    print("Failed to load model with all available methods")
    sys.exit(1)

load_model()

def get_model():
    global model
    if model is None:
        load_model()
    return model
