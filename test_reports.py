import requests
import sys
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import re

def test_reports_page():
    """Test if the reports page loads correctly"""
    
    # Login URL
    login_url = 'http://127.0.0.1:8000/login/'
    reports_url = 'http://127.0.0.1:8000/reports/'
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # 1. Get the login page to retrieve CSRF token
        login_response = session.get(login_url)
        login_response.raise_for_status()
        
        # Parse the login page
        login_soup = BeautifulSoup(login_response.text, 'html.parser')
        
        # Extract CSRF token
        csrf_token = login_soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if not csrf_token:
            print("ERROR: Could not find CSRF token. Aborting.")
            return False
        
        # 2. Login with test credentials
        login_data = {
            'csrfmiddlewaretoken': csrf_token['value'],
            'username': 'testadmin',  # Updated to use the superuser we created
            'password': 'testadmin123',
        }
        
        login_post_response = session.post(login_url, data=login_data, headers={
            'Referer': login_url
        })
        
        # Check if login was successful
        if 'login' in login_post_response.url.lower():
            print("ERROR: Login failed. Check credentials.")
            return False
        
        print("Login successful!")
        
        # 3. Access the reports page
        reports_response = session.get(reports_url)
        reports_response.raise_for_status()
        
        # Parse the reports page
        reports_soup = BeautifulSoup(reports_response.text, 'html.parser')
        
        # 4. Check if the page has the expected elements
        charts = reports_soup.find_all('canvas')
        stat_cards = reports_soup.find_all('div', {'class': re.compile('.*border-l-4.*')})
        
        # Print results
        print(f"Status Code: {reports_response.status_code}")
        print(f"Charts Found: {len(charts)}")
        print(f"Stat Cards Found: {len(stat_cards)}")
        
        # Print page title to help debug
        title = reports_soup.find('title')
        if title:
            print(f"Page Title: {title.text}")
        
        if len(charts) >= 4 and len(stat_cards) >= 4:
            print("SUCCESS: Reports page loaded successfully with expected elements")
            return True
        else:
            print("ERROR: Reports page is missing expected elements")
            # Print some of the page content for debugging
            print("Page Content Sample:")
            main_content = reports_soup.find('div', {'class': 'container'})
            if main_content:
                print(main_content.text[:500] + "...")
            else:
                print(reports_soup.text[:500] + "...")
            return False
        
    except RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return False

if __name__ == "__main__":
    if test_reports_page():
        sys.exit(0)
    else:
        sys.exit(1) 