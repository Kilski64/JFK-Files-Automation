import requests
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm  # For progress bar

RELEASE_URL = "https://www.archives.gov/research/jfk/release-2025"

def create_directory():
    """Create a directory to store downloaded PDFs"""
    folder_name = r"INSERT FILE PATH"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def get_pdf_links(url):
    """Scrape the webpage for PDF links"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf'):
                if not href.startswith('http'):
                    href = 'https://www.archives.gov' + href
                pdf_links.append(href)
        return pdf_links
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []

def download_pdf(url, folder):
    """Download a single PDF file and return status"""
    try:
        filename = url.split('/')[-1]
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            return f"Skipped {filename} - already exists"
        
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Downloaded {filename}"
    
    except requests.RequestException as e:
        return f"Failed {url}: {e}"

def download_all_pdfs(pdf_links, folder, max_workers=10):
    """Download all PDFs concurrently with a thread pool"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_url = {executor.submit(download_pdf, url, folder): url for url in pdf_links}
        
        # Show progress bar
        results = []
        for future in tqdm.tqdm(as_completed(future_to_url), total=len(pdf_links), desc="Downloading PDFs"):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(f"Error: {e}")
        
        return results

def main():
    # Create download directory
    download_folder = create_directory()
    
    # Scrape PDF links
    print(f"Scraping {RELEASE_URL} for PDF links...")
    pdf_links = get_pdf_links(RELEASE_URL)
    
    if not pdf_links:
        print("No PDF links found.")
        return
    
    print(f"Found {len(pdf_links)} PDF files to download")
    
    # Download all PDFs concurrently
    results = download_all_pdfs(pdf_links, download_folder)
    
    # Print summary
    print("\nDownload Summary:")
    for result in results:
        print(result)
    
    print(f"\nDownload complete! Files are in {download_folder}")

if __name__ == "__main__":
    try:
        import requests
        import bs4
        import tqdm
    except ImportError:
        print("Please install required libraries:")
        print("pip install requests beautifulsoup4 tqdm")
        exit(1)
    main()