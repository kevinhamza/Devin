import requests
from bs4 import BeautifulSoup
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

def banner():
    print("""
    ==============================================
       Advanced Penetration Testing and Bug Hunting Tool
    ==============================================
    Disclaimer: Use responsibly and only on websites
    you have explicit permission to test.
    ==============================================
    """)

def fetch_urls(target_url):
    """Fetch all URLs from a target website."""
    try:
        response = requests.get(target_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        urls = [link.get('href') for link in soup.find_all('a', href=True)]
        print(f"[+] Found {len(urls)} URLs on {target_url}")
        return urls
    except Exception as e:
        print(f"[-] Failed to fetch URLs: {e}")
        return []

def scan_ports(ip):
    """Scan open ports on a target IP."""
    print(f"\n[+] Scanning ports on {ip}...")
    open_ports = []
    for port in range(1, 1025):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            if result == 0:
                print(f"[+] Open port detected: {port}")
                open_ports.append(port)
            sock.close()
        except Exception as e:
            print(f"[-] Error scanning port {port}: {e}")
    return open_ports

def detect_vulnerabilities(url):
    """Basic vulnerability detection."""
    vulns = {}
    try:
        response = requests.get(url, timeout=10)
        if re.search(r'<script>.*</script>', response.text, re.IGNORECASE):
            vulns['XSS'] = True
        if re.search(r'(\bSELECT\b|\bUNION\b|\bINSERT\b|\bUPDATE\b)', response.text, re.IGNORECASE):
            vulns['SQL Injection'] = True
    except Exception as e:
        print(f"[-] Failed to check {url}: {e}")
    return vulns

def subdomain_enumeration(domain):
    """Enumerate subdomains using Assetfinder."""
    subdomains = []
    try:
        result = subprocess.run(['assetfinder', '--subs-only', domain], capture_output=True, text=True)
        subdomains = result.stdout.splitlines()
        for subdomain in subdomains:
            print(f"[+] Subdomain found: {subdomain}")
    except Exception as e:
        print(f"[-] Subdomain enumeration failed: {e}")
    return subdomains

def run_nmap_scan(ip):
    """Run an Nmap scan on a target IP."""
    print("\n[+] Running Nmap scan...")
    try:
        result = subprocess.check_output(["nmap", "-sV", ip], universal_newlines=True)
        print(result)
    except Exception as e:
        print(f"[-] Failed to run Nmap scan: {e}")

def main():
    banner()
    target = input("Enter target URL (e.g., https://example.com): ").strip()
    parsed_url = urlparse(target)
    domain = parsed_url.netloc or parsed_url.path
    ip = socket.gethostbyname(domain)

    print(f"\n[+] Target IP: {ip}")

    # Fetch URLs
    urls = fetch_urls(target)

    # Subdomain Enumeration
    subdomains = subdomain_enumeration(domain)

    # Port Scanning
    open_ports = scan_ports(ip)

    # Run Nmap Scan
    run_nmap_scan(ip)

    # Vulnerability Detection
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(detect_vulnerabilities, url): url for url in urls}
        for future in futures:
            url = futures[future]
            try:
                vulns = future.result()
                if vulns:
                    print(f"[!] Vulnerabilities detected on {url}: {vulns}")
            except Exception as e:
                print(f"[-] Error checking {url}: {e}")

if __name__ == "__main__":
    main()
