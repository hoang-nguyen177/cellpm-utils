import yaml, json
import logging
import os, re
import argparse                                                                 
import requests

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
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response

def main():
    parser = argparse.ArgumentParser(prog='utils')
    parser.add_argument("-c", "--config-file", dest="config", required=True,
                    help="config file name", metavar="FILE")

    args = parser.parse_args()

    if not os.path.exists(args.config):
        logging.error(f"Config file {args.config} does not exists")
        exit(1)

    with open(args.config, "r") as configf:
        try:
            config_obj = yaml.safe_load(configf)
        except yaml.YAMLError as exc:
            logging.error("Invalid resource config file")
            logging.error(exc)
            logging.error(1)
    if config_obj:
        success = {}
        fails = {}
        final_result={}
        for file in config_obj['files']:
            logging.info(f"File={file['pdbFile']} membrancetype={file['membraneType']} temp={file['temperature']} ph={file['ph']}")
            resp = request(file['pdbFile'], file['membraneType'], file['temperature'], file['ph'])
            if resp.status_code == 200:
                success[file['pdbFile']] = resp.text
            else:
                fails[file['pdbFile']] = resp.text
        #### 
        logging.info(">>>>Failed:")
        for file in fails:
            resp_json = json.loads(fails[file])
            logging.info(f"file={file} response={resp_json['message']}")
            logging.info(resp_json)
        import time
        time.sleep(10)
        logging.info(">>>>Success:")
        for file in success:
            resp_json = json.loads(success[file])
            logging.info(f"file={file} response={resp_json['message']}")
            result_resp = get_result(resp_json['resultsUrl'])
            if result_resp.status_code == 200:
                # start parsing text
                occurrences = re.findall(r'Log of permeability coefficient=.*\d+', result_resp.text)
                if len(occurrences) > 0:
                    value = float(occurrences[0].split("=")[1])
                    final_result[file] = value
        logging.info(">>>>Final results")
        logging.info(final_result)

            
        
if __name__ == "__main__":
    main()