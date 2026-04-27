import requests
import sys
import argparse
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

found_results = []
baseline_length = None
baseline_title = None

def get_title(text):
    start = text.lower().find("<title>")
    end = text.lower().find("</title>")
    if start != -1 and end != -1:
        return text[start + 7:end].strip()
    return ""

def scan_path(base_url, path):
    global baseline_length, baseline_title

    url = urljoin(base_url + "/", path.strip())
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        elapsed = round(time.time() - start_time, 2)

        length = len(response.text)
        title = get_title(response.text)
        status = response.status_code

        if length == baseline_length and title == baseline_title:
            return

        if status == 200:
            slow_tag = ""
            if elapsed > 2:
                slow_tag = "[SLOW] "

            result = f"{slow_tag}[{status}] {url} -> title: {title} -> length: {length} -> time: {elapsed}s"
            print(result)
            found_results.append(result)

    except:
        pass

def run_scan(args):
    global baseline_length, baseline_title

    print("Starting scan...\n")

    fake_path = str(random.randint(100000, 999999))
    fake_url = urljoin(args.url + "/", fake_path)

    try:
        fake_response = requests.get(fake_url, timeout=5)
        baseline_length = len(fake_response.text)
        baseline_title = get_title(fake_response.text)

        print(f"[BASELINE] length: {baseline_length}")
        print(f"[BASELINE] title: {baseline_title}\n")

    except:
        print("Failed to get baseline.")
        return

    try:
        with open(args.wordlist, "r") as f:
            paths = f.readlines()
    except:
        print("Wordlist file not found.")
        return

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        executor.map(lambda p: scan_path(args.url, p), paths)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for line in found_results:
                f.write(line + "\n")
        print(f"\nResults saved to {args.output}")

    print("\nScan finished.")

def interactive_mode():
    url = input("Enter target URL: ")
    threads = int(input("Enter thread count (default 20): ") or 20)
    wordlist = input("Enter wordlist file (default wordlist.txt): ") or "wordlist.txt"
    output = input("Enter output file (optional): ")

    class Args:
        pass

    args = Args()
    args.url = url
    args.threads = threads
    args.wordlist = wordlist
    args.output = output if output else None

    run_scan(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Directory Scanner Tool")
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Thread count")
    parser.add_argument("-w", "--wordlist", default="wordlist.txt", help="Wordlist file")
    parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    if not args.url:
        print("No arguments detected. Switching to interactive mode.\n")
        interactive_mode()
    else:
        run_scan(args)