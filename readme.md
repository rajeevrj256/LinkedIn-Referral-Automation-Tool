
# Linkedin Referral Automation tool

The Referral Automation Tool is an AI-powered Chrome extension designed to streamline the process of requesting referrals on LinkedIn. Built using GPT-4, Selenium, and NLP techniques, the tool personalizes outreach messages based on a user’s profile and automates message delivery at scale — significantly reducing manual effort while maintaining a human-like touch.


## Features

- GPT-4–Powered Message Generation: Automatically crafts personalized referral messages using contextual input like user role, company, and mutual connections.
- Selenium Automation: Navigates LinkedIn profiles, detects whether messaging is available, and sends connection or referral requests without user intervention.
- Dynamic Profile Parsing: Extracts relevant details from profiles (e.g., position, headline, mutuals) to tailor messages for better engagement.
- Bulk Outreach Capability: Sends context-aware messages to 30+ connections in a single session, enabling efficient and scalable networking.
- Time Efficiency: Reduces manual effort by 80%, making the referral outreach process fast, personalized, and scalable.

- Failsafe Mechanisms: Skips accounts where messaging is restricted or duplicate requests exist, ensuring safe and clean execution.




## Installation



```bash
  git clone
  cd LinkedIn-Referral-Automation-Tool
```
Installation Packages/Lib

```bash
pip install requirements.txt

```

Add .env File:

```bash
LINKEDIN_EMAIL="You LinkedIn account Id"
LINKEDIN_PASSWORD="You LinkedIn account password"
OPENAI_API_KEY="you api key"
```

Run:

```bash
python referrals

```
## Demo


https://www.linkedin.com/posts/rajiv-ranjan256_python-openai-gpt4-activity-7335160605974097920-0a7A?utm_source=share&utm_medium=member_desktop&rcm=ACoAADf0T70Bk7NqSHsc25zaRqwpjhTNNScyio0