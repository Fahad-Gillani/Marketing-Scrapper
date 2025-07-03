import streamlit as st
from googlesearch import search
import requests
import re
import pandas as pd
import time

# ---------------------------
# 🔍 Google Search Function
# ---------------------------
def get_sites(query, region, max_results=10):
    full_query = f"{query} in {region}"
    links = []
    try:
        for url in search(full_query, num_results=max_results):
            if url and url not in links:
                links.append(url)
        return links
    except Exception:
        return []

# ---------------------------
# 📧 Email Extractor
# ---------------------------
def extract_emails_from_url(url, allowed_domains=None):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        raw_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", response.text)
        emails = [
            email for email in set(raw_emails)
            if not re.search(r'\.(png|jpg|jpeg|gif|svg|webp|css|js|ico|woff|ttf|otf)(\?|$)', email)
            and not re.search(r'@[0-9]+\.[0-9]+', email)
        ]
        if allowed_domains:
            emails = [email for email in emails if email.split('.')[-1].lower() in allowed_domains]
        return emails
    except Exception:
        return []

# ---------------------------
# 🌐 Streamlit App
# ---------------------------
st.set_page_config(page_title="📧 Email Scraper", layout="wide")
st.title("📧 Email Scraper for Lead Generation")
st.markdown("Use Google to search websites by topic and region, then extract public emails for marketing or outreach.")

st.divider()

# ---------------------------
# 📝 Input Section
# ---------------------------
with st.form("email_scraper_form"):
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("🔍 What are you looking for?", placeholder="e.g., SEO agencies, fitness trainers")
    with col2:
        region_input = st.text_input("🌍 Regions (comma-separated)", placeholder="e.g., USA, UK, Germany")

    st.markdown("#### ✂️ Filter by Email Domain")
    selected_domains = st.multiselect(
        "Allowed Domains (optional):",
        options=["com", "org", "net", "ch", "uk", "de", "fr", "it", "pk"]
    )

    max_results = st.slider("🔗 Number of Websites per Region:", 5, 30, 10)

    submitted = st.form_submit_button("🚀 Find Emails")

# ---------------------------
# 🚀 Main Execution
# ---------------------------
if submitted:
    if not search_query or not region_input:
        st.warning("⚠️ Please enter both a search topic and at least one region.")
    else:
        regions = [r.strip() for r in region_input.split(",") if r.strip()]
        all_data = []
        all_valid_emails = []
        seen_emails = set()  # ✅ Deduplication set

        with st.spinner("🔄 Scraping in progress..."):
            for region in regions:
                st.subheader(f"📍 Searching for **{search_query}** in _{region}_")
                urls = get_sites(search_query, region, max_results)
                region_data = []
                progress = st.progress(0, text=f"Processing websites for {region}...")

                for i, url in enumerate(urls):
                    emails = extract_emails_from_url(url, selected_domains if selected_domains else None)
                    if emails:
                        for email in emails:
                            if email not in seen_emails:
                                seen_emails.add(email)
                                entry = {"Search": search_query, "Region": region, "Website": url, "Email": email}
                                region_data.append(entry)
                                all_valid_emails.append(entry)
                    else:
                        region_data.append({
                            "Search": search_query, "Region": region,
                            "Website": url, "Email": "No emails found"
                        })
                    time.sleep(1)
                    progress.progress((i + 1) / len(urls), text=f"{region}: {i + 1}/{len(urls)} scraped")

                st.dataframe(pd.DataFrame(region_data))
                all_data.extend(region_data)
        # ---------------------------
        # 📥 CSV Download
        # ---------------------------
        if all_valid_emails:
            df_valid = pd.DataFrame(all_valid_emails)
            st.success(f"✅ Extracted **{len(df_valid)}** valid emails across **{len(regions)}** region(s).")

            csv = df_valid.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Valid Emails as CSV",
                data=csv,
                file_name="marketing_email_list.csv",
                mime="text/csv",
            )
        else:
            st.warning("⚠️ No valid emails were found.")