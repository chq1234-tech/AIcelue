import subprocess
import time
import webbrowser
import os

def main():
    print("=" * 60)
    print("      Dividend ETF DCA System - One Click Investment")
    print("=" * 60)
    print()
    
    # Step 1: Execute DCA investment
    print("[Step 1/3] Executing monthly DCA investment...")
    print("=" * 60)
    result = subprocess.run(["python", "dca_main.py", "run"], capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("=" * 60)
    print()
    
    # Step 2: Start web server in background
    print("[Step 2/3] Starting Web server...")
    web_process = subprocess.Popen(["python", "dca_web.py"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("Waiting for web server to start...")
    time.sleep(3)
    
    # Step 3: Open browser
    print("[Step 3/3] Opening web browser...")
    url = "http://localhost:8080"
    webbrowser.open(url)
    
    print()
    print("=" * 60)
    print("DCA Investment Completed!")
    print(f"Web page: {url}")
    print("Press Enter to exit...")
    input()
    
    # Clean up
    web_process.terminate()

if __name__ == "__main__":
    main()