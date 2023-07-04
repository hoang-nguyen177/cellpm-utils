import yaml, json
import logging
import os, re
import argparse                                                                 
import requests
import time

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

url = "https://cgopm.cc.lehigh.edu/cellpm"


def request(filepath, membranetype, temp, ph):
    payload={
        "membraneType": membranetype,
        "temperature": temp,
        "ph": ph
    }
    
    files=[
        ('pdbFile',(os.path.basename(filepath),open(filepath,'rb'),'application/octet-stream'))
    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    return response

def get_result(url):
    logging.info(f"Requesting {url}")
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response

def main():
    parser = argparse.ArgumentParser(prog='utils')
    parser.add_argument("-i", "--input-file", dest="input", required=True,
                    help="input file name", metavar="FILE")
    parser.add_argument("--ph", dest="ph", default=7, required=True, help="ph")
    parser.add_argument("--membrane-type", dest="membranetype", default='DOPC', required=True, help="membraneType")
    parser.add_argument("--temperature", dest="temperature", default=300, required=True, help="temperature")
    # parser.add_argument("--batch-size", dest="batchsize", default=2, help="size of batches")
    parser.add_argument("--sleep", dest="sleep", default=20, help="sleep time in seconds")
    parser.add_argument("-o", "--output-file", dest="output", default='output.txt', required=True, help="output file name", metavar="FILE")
    parser.add_argument("-e", "--error-file", dest="error", default='error.txt', required=True, help="error file name", metavar="FILE")
    

    args = parser.parse_args()

    logging.info(f"membrancetype={args.membranetype} temp={args.temperature} ph={args.ph}")

    if not os.path.exists(args.input):
        logging.error(f"Config file {args.input} does not exists")
        exit(1)

    outputf = open(args.output, 'w')
    outputf.write(f"File, Log of permeability coefficient\n")
    errorf = open(args.error, 'w')
    errorf.write(f"File, type, code, url, message\n")
    resultsf = open("results.txt", 'w')
    resultsf.write(f"File, ResultUrl, Status\n") # status =1 success, 0 fail
    results = {}
    with open(args.input, "r") as inputf:
        line = inputf.readline()
        while line != '':
            line = line.strip()
            if os.path.exists(line):
                logging.info(f"File={line}")
                try:
                    resp = request(line, args.membranetype, args.temperature, args.ph)
                    resp_json = json.loads(resp.text)
                    if resp.status_code == 200:
                        logging.info(f"file={line} success response={resp_json['message']} resultUrl={resp_json['resultsUrl']}")
                        resultsf.write(f"{line}, {resp_json['resultsUrl']}, 1\n")
                        results[line] = resp_json['resultsUrl']
                        time.sleep(1)
                    else:
                        # fail
                        resultsf.write(f"{line}, {resp_json['resultsUrl']}, 0\n")
                        errorf.write(f"{line}, submission, {resp.status_code}, {url}, {resp_json['message']}\n")
                except Exception as e:
                    logging.error(f"Error: {e}")
            else:
                logging.info(f"File={line} does not exist")
            line = inputf.readline()
    logging.info("Sleep to let server to run")
    time.sleep(args.sleep)
    for line in results:
        # success
        result_resp = get_result(results[line])
        if result_resp.status_code == 200:
            # start parsing text
            occurrences = re.findall(r'Log of permeability coefficient=.*\w+', result_resp.text)
            logging.info(f"Processing {line}. Occurences: {occurrences}")
            if len(occurrences) > 0:
                value = occurrences[0].split("=")[1].strip()
                outputf.write(f"{line},{value}\n")
        else:
            logging.error(f">>>>{line} Failed , {result_resp.status_code}, {result_resp.text}")
            errorf.write(f"{line}, result, {result_resp.status_code}, {resp_json['resultsUrl']}, {result_resp.text}\n")
    logging.info(f">>>>Results written to {args.output} Errors written to {args.error}")
    resultsf.close()
    outputf.close()
    errorf.close()
 
            
        
if __name__ == "__main__":
    main()