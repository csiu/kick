import argparse
from bs4 import BeautifulSoup
import requests
import zipfile
import io
import os
import glob
import datetime

usage = """
Download Kickstarter data from https://webrobots.io/kickstarter-datasets/
"""

def getargs():
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument('datadir', help="/dir/path to store downloaded files")
    args = parser.parse_args()
    return args

def download_zipfile(zip_file_url, download_dir):
    r = requests.get(zip_file_url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(download_dir)

def convert_str2date(yyyymmdd):
    return(datetime.datetime.strptime(yyyymmdd, '%Y-%m-%d'))

def ensure_dir(directory):
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return(directory)

class DownloadData:
    def __init__(self, datadir):
        self.url = "https://webrobots.io/kickstarter-datasets"
        self.download_dir = ensure_dir(datadir)

    def _check_latest(self):
        """
        Returns (1) the latest date data was scrapped & (2) link to CSV file
        """
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, "html5lib")

        latest = soup.body.find("div", {"id": "main"}).find("li")
        latest_date = latest.text.split(' ', 1)[0]
        latest_json, latest_csv = [v["href"] for v in latest.find_all("a")]

        self.webrobot_date = latest_date
        self.webrobot_file = latest_csv
        return(self)

    def _download(self):
        """
        Download CSV file to download_dir and add a version
        """
        # Download files
        download_zipfile(self.webrobot_file, self.download_dir)

        # Tag the downloaded version
        download_version = "_version." + self.webrobot_date
        download_version = os.path.join(self.download_dir, download_version)
        open(download_version, 'a').close()

    def _check_data_download(self):
        if os.path.exists(self.download_dir):
            version = glob.glob(os.path.join(self.download_dir, "_version.*"))
            if version:
                version = os.path.basename(version[0]).split(r".", 1)[1]
                return(version)
            else:
                return(None)
        else:
            return(None)

    def get(self):
        self = self._check_latest()

        date_latest = self.webrobot_date
        date_download = self._check_data_download()

        if date_download is None:
            print("Downloading version:'%s'..." % date_latest)
            self._download()
        else:
            # Convert to date objects
            date_latest = convert_str2date(date_latest)
            date_download = convert_str2date(date_download)

            # latest date is newer than scrape date then Download
            # else do nothing
            if date_latest > date_download:
                print("Downloading version:'%s'..." % date_latest)
                self._download()
            else:
                print("Nothing to do;",
                      "latest version:'%s' is already downloaded" %
                      date_latest.date())

if __name__ == '__main__':
    args = getargs()
    DownloadData(args.datadir).get()
