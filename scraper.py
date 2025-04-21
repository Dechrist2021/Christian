import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import base64
import os

# ==============================================
# Beautiful UI Setup
# ==============================================
st.set_page_config(
    page_title="Hotels Reviews Scraper",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful interface
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .stTextInput>div>div>input {
        border: 2px solid #4a90e2;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #4a90e2;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #357abd;
        transform: scale(1.02);
    }
    .stProgress>div>div>div>div {
        background-color: #4a90e2;
    }
    .stDataFrame {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .download-link {
        display: inline-block;
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        margin-top: 20px;
        transition: all 0.3s;
    }
    .download-link:hover {
        background-color: #218838;
        transform: scale(1.02);
        color: white;
        text-decoration: none;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================
# App Header
# ==============================================
st.image("https://maps.gstatic.com/tactile/images/maps_logo_grayscale-4b0a256a.png", width=150)
st.title("🗺️ Hotels Reviews Scraper")
st.markdown("Extract all reviews from any Google Maps location with one click.")

# ==============================================
# Core Functionality (Your Working Code)
# ==============================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    
    # Cloud configuration (only)
    chrome_options.binary_location = "/usr/bin/google-chrome"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=chrome_options)

if 'reviews' not in st.session_state:
    st.session_state.reviews = None

def scrape_reviews(url):
    driver = get_driver()
    
    try:
        # Initial setup
        progress_bar.progress(5)
        status_text.markdown("🚀 **Launching browser...**")
        driver.get(url)
        time.sleep(3)  # Initial load wait

        # Accept cookies (multiple possible selectors)
        try:
            cookie_buttons = [
                "[aria-label*='Accept all']",
                "[aria-label*='Accept']",
                "button:contains('Accept')",
                "button:contains('I agree')"
            ]
            for selector in cookie_buttons:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    ).click()
                    progress_bar.progress(10)
                    status_text.markdown("✅ **Cookies accepted**")
                    time.sleep(1)
                    break
                except:
                    continue
        except:
            pass

        # Find reviews section
        progress_bar.progress(15)
        status_text.markdown("🔍 **Finding reviews section...**")
        try:
            review_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-review-id]")))
        except:
            st.error("Could not find reviews section. Please make sure this is a valid Google Maps place page with reviews.")
            return []

        # Scroll to load all reviews
        last_height = driver.execute_script("return arguments[0].scrollHeight", review_section)
        scroll_attempt = 0
        
        while scroll_attempt < 50:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", review_section)
            time.sleep(2.5)  # Increased wait time for loading
            
            # Update progress
            scroll_progress = min(15 + int((scroll_attempt/50) * 55, 70))
            progress_bar.progress(scroll_progress)
            
            current_reviews = len(driver.find_elements(By.CSS_SELECTOR, 'div[data-review-id]'))
            status_text.markdown(f"📜 **Loaded {current_reviews} reviews...**")
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", review_section)
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempt += 1

        # Extract reviews
        progress_bar.progress(75)
        status_text.markdown("🔄 **Processing reviews...**")
        all_reviews = []
        reviews = driver.find_elements(By.CSS_SELECTOR, "div[data-review-id]")
        
        for i, review in enumerate(reviews):
            try:
                # RATING EXTRACTION (fraction format)
                rating = "N/A"
                try:
                    # Look for the fraction format (like "5/5")
                    rating_div = review.find_element(By.CSS_SELECTOR, "div.fontBodySmall")
                    rating_text = rating_div.text.strip()
                    if '/' in rating_text:
                        rating = rating_text.split('/')[0].strip()
                except:
                    pass
                
                # REVIEW TEXT EXTRACTION
                text = ""
                try:
                    text_el = review.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                    text = text_el.text if text_el else ""
                except:
                    pass
                
                # Only add if we have either rating or text
                if rating != "N/A" or text.strip():
                    all_reviews.append({
                        "Rating": rating,
                        "Review": text
                    })
                    
            except Exception as e:
                print(f"Skipped review due to error: {str(e)}")
                continue
            
            # Update progress
            if reviews:
                progress_bar.progress(75 + int((i/len(reviews)) * 25))

        return all_reviews

    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")
        return []
    finally:
        try:
            driver.quit()
        except:
            pass

def get_download_link(df):
    # Convert ratings to numeric (keeping "N/A" as NaN)
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    # Generate CSV (NaN will appear as empty in CSV)
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    filename = f"google_reviews_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    return f'''
    <a class="download-link" href="data:file/csv;base64,{b64}" download="{filename}">
        💾 Download CSV ({len(df)} reviews)
    </a>
    '''
# ==============================================
# Beautiful UI Components
# ==============================================
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input(
            "Paste Google Maps URL:",
            placeholder="Paste Google Maps URL...",
            label_visibility="collapsed"
        )
    with col2:
        st.write("")  # Spacer
        scrape_btn = st.button("🚀 Scrape Reviews")

# Progress elements
progress_bar = st.progress(0)
status_text = st.empty()

# Main app logic
if scrape_btn and url:
    if not url.startswith("https://www.google.com/maps"):
        st.error("Please enter a valid Google Maps URL")
    else:
        try:
            reviews = scrape_reviews(url)
            st.session_state.reviews = pd.DataFrame(reviews)
            
            with st.container():
                st.markdown(f"""
                <div class="success-box">
                    ✨ <strong>Success!</strong> Found {len(reviews)} reviews
                </div>
                """, unsafe_allow_html=True)
                
                st.dataframe(
                    st.session_state.reviews,
                    height=300,
                    use_container_width=True
                )
                
                if not st.session_state.reviews.empty:
                    st.markdown(get_download_link(st.session_state.reviews), unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            progress_bar.progress(0)
            status_text.text("")

# Reset button
# ==============================================
# Clear Results Button (Fixed Version)
# ==============================================
if st.session_state.reviews is not None:
    if st.button("🔄 Clear Results"):
        st.session_state.reviews = None
        progress_bar.progress(0)
        status_text.text("")
        
        # Add a small delay and success message
        with st.spinner("Clearing data..."):
            time.sleep(0.5)
        st.success("Data cleared successfully!")
        
        # Modern rerun approach
        st.rerun()

# ==============================================
# Help Section
# ==============================================
with st.expander("ℹ️ How to use this tool"):
    st.markdown("""
    1. **Find a place** on Google Maps in your browser
    2. **Copy the full URL** from the address bar
    3. **Paste it above** and click "Scrape Reviews"
    4. **Download your data** as CSV when finished
    
    💡 **Tip:** The more reviews a place has, the longer scraping will take
    """)

st.markdown("---")
st.markdown("""
<style>
    .footer {
        text-align: center;
        padding: 10px;
        color: #6c757d;
        font-size: 0.9em;
    }
</style>
<div class="footer">
    Made with ❤️ using Streamlit | Google Maps Reviews Scraper Pro
</div>
""", unsafe_allow_html=True)
