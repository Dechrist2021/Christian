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
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    import os

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    # Streamlit Cloud paths (from setup.sh)
    if os.path.exists('/usr/bin/chromedriver'):
        chrome_options.binary_location = '/usr/bin/google-chrome'
        service = Service('/usr/bin/chromedriver')
    else:
        # Local fallback (Windows/Mac)
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=chrome_options)

if 'reviews' not in st.session_state:
    st.session_state.reviews = None

def scrape_reviews(url):
    driver = get_driver()
    
    try:
        # Update progress
        progress_bar.progress(5)
        status_text.markdown("🚀 **Launching browser...**")
        
        driver.get(url)
        
        # Accept cookies
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label*='Accept all']"))
            ).click()
            progress_bar.progress(10)
            status_text.markdown("✅ **Cookies accepted**")
            time.sleep(1)  # Small delay after clicking
        except:
            pass
        
        # Scroll to load reviews
        progress_bar.progress(15)
        status_text.markdown("🔍 **Finding reviews section...**")
        
        review_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"))
        )
        
        last_height = 0
        scroll_attempt = 0
        
        while scroll_attempt < 30:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", review_section)
            time.sleep(2)
            
            scroll_progress = 15 + int((scroll_attempt/30) * 55)
            progress_bar.progress(scroll_progress)
            status_text.markdown(f"📜 **Loading reviews...** ({len(driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf'))} found)")
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", review_section)
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempt += 1
        
        # Extract reviews
        progress_bar.progress(75)
        status_text.markdown("🔄 **Processing reviews...**")
        
        all_reviews = []
        reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        
        for i, review in enumerate(reviews):
            progress_bar.progress(75 + int((i/len(reviews)) * 25))
            
            try:
                # More robust rating extraction
                rating = "N/A"
                
                # Try getting star rating first
                try:
                    rating_element = review.find_element(By.CSS_SELECTOR, "span.fzvQIb")
                    aria_label = rating_element.get_attribute('aria-label')
                    if aria_label:
                        # Extract just the number (e.g., "3 stars" -> "3")
                        rating = aria_label.split(' ')[0]
                except:
                    pass
                
                # If no star rating found, try fraction format (like "5/5")
                if rating == "N/A":
                    try:
                        rating_div = review.find_element(By.CSS_SELECTOR, "div.fontBodySmall")
                        rating_text = rating_div.text
                        if '/' in rating_text:
                            rating = rating_text.split('/')[0].strip()
                    except:
                        pass
                
                # Extract review text
                text_elements = review.find_elements(By.CSS_SELECTOR, "span.wiI7pd")
                text = text_elements[0].text if text_elements else ""
                
                # Only add if we have valid data
                if rating != "N/A" or text.strip():
                    all_reviews.append({
                        "Rating": rating,
                        "Review": text
                    })
            except Exception as e:
                print(f"Skipping review due to error: {str(e)}")
                continue
                
        return all_reviews
        
    finally:
        driver.quit()

def get_download_link(df):
    # Ensure rating column is numeric for better sorting
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
    csv = df.to_csv(index=False, encoding='utf-8-sig')  # utf-8-sig for Excel compatibility
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    filename = f"google_reviews_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return f'<a class="download-link" href="data:file/csv;base64,{b64}" download="{filename}">💾 Download CSV ({len(df)} reviews)</a>'
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
