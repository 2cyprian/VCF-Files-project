import requests
from bs4 import BeautifulSoup
import re

def extract_business_info(url):
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    # Business Name (try title, h1, or og:title)
    name = ''
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        name = og_title['content'].strip()
    elif soup.title and soup.title.string:
        name = soup.title.string.strip()
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        name = h1.get_text(strip=True)
    # Phone
    phones = list(set(re.findall(r'\+?\d[\d\s\-()]{7,}\d', text)))
    # Email
    emails = list(set(re.findall(r'[\w\.-]+@[\w\.-]+', text)))
    # Address (look for address tag or common patterns)
    address = ''
    addr_tag = soup.find('address')
    if addr_tag:
        address = addr_tag.get_text(separator=' ', strip=True)
    else:
        addr_match = re.search(r'\d{1,5} [\w\s\.,-]+(Street|St|Avenue|Ave|Road|Rd|Block|Plaza|Building|House|PO Box)[\w\s\.,-]*', text, re.IGNORECASE)
        if addr_match:
            address = addr_match.group(0)
    # Website (if not the same as input)
    website = ''
    for a in soup.find_all('a', href=True):
        if 'http' in a['href'] and url not in a['href']:
            website = a['href']
            break
    # Social links
    socials = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'facebook.com' in href:
            socials['facebook'] = href
        elif 'instagram.com' in href:
            socials['instagram'] = href
        elif 'twitter.com' in href:
            socials['twitter'] = href
        elif 'linkedin.com' in href:
            socials['linkedin'] = href
    # Description/About
    desc = ''
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and desc_tag.get('content'):
        desc = desc_tag['content']
    # Extract list of business/school entries with names and links
    entries = []
    for a in soup.find_all('a', href=True):
        entry_name = a.get_text(strip=True)
        entry_link = a['href']
        # Heuristic: skip navigation, social, or empty links
        if not entry_name or entry_name.lower() in ['home', 'about', 'contact', 'privacy policy', 'terms of use']:
            continue
        # Only include links that look like business/school profiles (customize as needed)
        if ('school' in entry_link or 'business' in entry_link) and not entry_link.startswith('#'):
            # Make link absolute
            if not entry_link.startswith('http'):
                entry_link = requests.compat.urljoin(url, entry_link)
            entries.append({'name': entry_name, 'link': entry_link})
    # Only include non-empty fields
    result = {'source_url': url}
    if name: result['name'] = name
    if phones: result['phones'] = phones
    if emails: result['emails'] = emails
    if address: result['address'] = address
    if website: result['website'] = website
    if socials: result['socials'] = socials
    if desc: result['description'] = desc
    if entries: result['entries'] = entries
    return result
