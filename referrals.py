import time
import logging
import openai
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# Setup logging
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

# Update with your credentials
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")                          
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

openai.api_key = os.getenv("OPENAI_API_KEY") 

def get_search_url(company):
    return f"https://www.linkedin.com/search/results/people/?keywords={company}&network=%5B%22F%22%5D&origin=FACETED_SEARCH"


def generate_referral_message_ai(name, role, job_id, company, jd, candidate_skills, project, myname, resume):
    prompt = f"""
Write a short, polite, and friendly LinkedIn message to someone named {name} who works at {company}.
I, {myname}, am asking if they would consider referring me for the {role} position (Job ID: {job_id}) at their company.

The job description mentions:
{jd}

My background:
- Key skills: {', '.join(candidate_skills)}
- Notable project: {project}
- Resume: {resume}

Guidelines:
- Start with a warm greeting (e.g., "Hi {name}, I hope you're doing well!")
- Mention the role clearly and express your interest
- Highlight your background, skills, or project in a natural way
- Make a polite ask for referral support
- Include the resume link near the end
- Keep it natural and concise like a LinkedIn message
- Do NOT use placeholders like [your name] or [resume link]
- add some space between paragraphs
- No subject lines or email format — it's a LinkedIn DM
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a career advisor that helps craft effective LinkedIn referral requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return (
            f"Hi {name}, I hope you're doing well! I came across the {role} opening (Job ID: {job_id}) at {company} and it seems like a great fit with my background "
            f"in {', '.join(candidate_skills)}. I’ve worked on projects like {project} that align well with the role. "
            f"If you're open to it, I'd be truly grateful if you could refer me. Here's my resume: {resume}. Thanks a lot! – {myname}"
        )

    
# Initialize Chrome driver
def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument(r"--user-data-dir=/Users/user/Library/Application Support/Google/Chrome")
    # options.add_argument(r"--profile-directory=Default")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Log in to LinkedIn
def login_linkedin(driver):
    logging.info("🔍 Checking if already logged into LinkedIn...")
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(2)

    try:
        # Check for element only visible when logged in
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "global-nav"))
        )
        logging.info("✅ Already logged in. Skipping login step.")
        return
    except TimeoutException:
        logging.info("🔐 Not logged in. Proceeding with login...")

    # Proceed to login page
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)

    logging.info("✅ Logged in successfully.")


# Send messages to profiles with Message button

def close_all_message_popups(driver):
    # Try to find all possible close buttons for message popups
    close_buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "header.msg-overlay-conversation-bubble-header button.msg-overlay-bubble-header__control.artdeco-button.artdeco-button--circle.artdeco-button--muted.artdeco-button--1.artdeco-button--tertiary.ember-view"
    )

    close_buttons += driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Dismiss']")
    for btn in close_buttons:
        try:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except Exception:
            pass

def process_profiles_on_page(driver, role, job_id, company, jd, candidate_skills, project, myname, resume):
    logging.info("🔍 Extracting profiles and sending messages...")

    profiles = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/') and @data-test-app-aware-link]")
    logging.info(f"Found {len(profiles)} profile links.")

    for idx, profile in enumerate(profiles):
        try:
            container = profile.find_element(By.XPATH, "../../../../..")  # walk up to card container

            # Extract name
            try:
                name_element = container.find_element(By.XPATH, ".//span[@dir='ltr']")
                name = name_element.text.strip().split(" ")[0]
            except Exception:
                name = "there"

            # Locate and click Message button
            try:
                message_button = container.find_element(By.XPATH, ".//span[text()='Message']/ancestor::button")
                driver.execute_script("arguments[0].click();", message_button)
                logging.info(f"[{idx+1}] ✅ Message button clicked for {name}.")
            except NoSuchElementException:
                logging.warning(f"[{idx+1}] ❌ No Message button for {name}. Skipping.")
                continue
            except ElementClickInterceptedException as e:
                logging.error(f"[{idx+1}] ❌ Couldn't click Message for {name}: {e}")
                continue

            # Wait and fill message box
            try:
                input_boxes = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((
                    By.XPATH, "//div[contains(@class, 'msg-form__contenteditable') and @role='textbox']"
                )))
                
                if not input_boxes:
                    raise Exception("No message input boxes found.")

                # Always use the last one opened (bottom-most in DOM order)
                input_box = input_boxes[-1]
                
                driver.execute_script("arguments[0].focus(); arguments[0].innerHTML = '';", input_box)

                message_html = f"<p>{generate_referral_message_ai(name, role, job_id, company, jd, candidate_skills, project, myname, resume)}</p>"
                
                driver.execute_script("""
                    arguments[0].innerHTML = arguments[1];
                    arguments[0].dispatchEvent(new InputEvent('input', { bubbles: true }));
                """, input_box, message_html)
                
                logging.info(f"[{idx+1}] ✉️ Message typed for {name}.")

            except Exception as e:
                logging.error(f"[{idx+1}] ❌ Error preparing message box for {name}: {e}")
                continue

            # Click send
            try:
                send_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "button.msg-form__send-button.artdeco-button[type='submit']"
                )))
                driver.execute_script("arguments[0].click();", send_button)
                logging.info(f"[{idx+1}] 🚀 Message sent to {name}.")
            except TimeoutException:
                logging.error(f"[{idx+1}] ❌ Send button not clickable for {name}.")
                continue

            # Close popup
            time.sleep(1)
            try:
                close_all_message_popups(driver)  # Ensure all popups are closed before proceeding
                # Wait until no message popups are present
                time.sleep(1)
                logging.info(f"[{idx+1}] ❎ Closed message popup for {name}.")
            except Exception as e:
                logging.warning(f"[{idx+1}] ⚠️ Could not close message popup for {name}: {e}")
                break

            time.sleep(2)
            logging.info(f"[{idx+1}] ✅ Processed profile for {name}.")

        except Exception as e:
            logging.error(f"[{idx+1}] ⚠️ Unexpected error processing profile: {e}")
            break

    logging.info("✅ Finished processing all visible profiles.")

    logging.info("🔍 Extracting profiles and sending messages...")

    profiles = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/') and @data-test-app-aware-link]")
    logging.info(f"Found {len(profiles)} profile links.")

    logging.info("✅ Finished processing profiles.")

# Main function
def main():
    logging.info("🚀 Starting LinkedIn referral automation script...")
    
    try:
        company = "oracle"
        role = "Software Developer 1"
        job_id = "291903"
        jd = """
Job Description
Design, develop, troubleshoot and debug software programs for databases, applications, tools, networks etc.

Responsibilities
As a member of the software engineering division, you will use basic knowledge of software architecture to perform tasks associated with developing, debugging or designing software applications or operating systems according to provided design specifications. Build enhancements within an existing software architecture.
"""
        candidate_skills = "Python, backend development, data structures, algorithms, problem-solving, distributed systems, cloud computing, java full stack , reactjs , nodejs, aws, sql, nosql, data analysis, machine learning, software development lifecycle (SDLC), agile methodologies"
        project = """
The Database Query Assistant is an AI-powered tool designed to convert natural language input into optimized SQL queries, making data access more intuitive for non-technical users and more efficient for developers. Built using React.js, Python, LangChain, and OpenAI’s language models, the tool supports a microservices architecture that interfaces with PostgreSQL, MySQL, and Oracle databases. It features 16 RESTful APIs for handling input processing, query generation, execution, and result delivery. To enhance performance and scalability, Redis caching is integrated, enabling faster responses and reduced database load. Overall, the system improves query efficiency by 40%, offering a seamless and intelligent data querying experience.
"""
        myname = "Rajiv Ranjan"

        resume="https://drive.google.com/file/d/1By6R3D1dQZqyr4JFgOetRj_9TX1ytQiz/view"

        driver = init_driver()
        login_linkedin(driver)
        logging.info("Navigating to search URL...")
        SEARCH_URL = get_search_url(company)
       
        driver.get(SEARCH_URL)
        time.sleep(5)

        process_profiles_on_page(driver, role, job_id, company, jd, candidate_skills, project, myname, resume)
        logging.info("✅ All messages sent successfully.")

    finally:
        
        logging.info("🛑 Script finished. Browser closed.")

if __name__ == "__main__":
    main()
