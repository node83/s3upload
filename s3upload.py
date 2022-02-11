
import argparse
import configparser
import fnmatch
import logging
import os
import sys
import threading

import boto3
import s3transfer


class S3Uploader:

    def __init__(self, conf):
        self.conf = conf['config']
        self.files = self._collect_files(self.conf.get('source_path'), self.conf.get('trigger'))
        self._lock = threading.Lock()
        self._failures = []

        filename = self.conf.get('log_file')
        if filename is not None:
            logging.basicConfig(filename=filename, level=self.conf.get('log_level', 'info').upper(),
                                format="%(asctime)s\t%(levelname)s\t%(message)s")

    def run(self):
        for group in sorted(self.files):
            file_list = self.files[group]
            while len(file_list) > 0:
                self._failures = []
                self._upload_group(file_list)
                file_list = self._failures

    def _upload_group(self, files):
        num_threads = int(self.conf.get('num_threads', 10))
        thread_list = []

        while len(files) > 0:
            if len(thread_list) < num_threads:
                file = files.pop(0)
                thr = threading.Thread(target=self._upload_file, args=(file['source'], file['bucket'], file['target']))
                thread_list.append(thr)
                thr.start()
            else:
                thread_list = [t for t in thread_list if t.is_alive()]

        while any([t.is_alive() for t in thread_list]):
            pass

    def _upload_file(self, source, bucket, target):
        if self.isVerbose():
            print('Uploading %s to s3:/%s/%s' % (source, bucket, target))
        logging.info('Uploading %s to s3:/%s/%s' % (source, bucket, target))

        error = False
        try:
            session = boto3.session.Session(aws_access_key_id=self.conf.get('aws_access_key'),
                                            aws_secret_access_key=self.conf.get('aws_secret_key'),
                                            region_name=self.conf.get('aws_region_name'))
            client = session.client('s3')
            conf = s3transfer.TransferConfig(multipart_threshold=int(self.conf.get('multipart_threshold', 8388608)),
                                             max_concurrency=int(self.conf.get('max_concurrency', 20)),
                                             multipart_chunksize=int(self.conf.get('multipart_chunksize', 8388608)),
                                             num_download_attempts=5,
                                             max_io_queue=int(self.conf.get('max_io_queue', 100)))
            transfer = s3transfer.S3Transfer(client=client, config=conf)
            transfer.upload_file(filename=source, bucket=bucket, key=target)
        except Exception as e:
            with self._lock:
                if self.isVerbose():
                    print('Failed uploading %s; requeueing' % source)
                logging.warning('Failed uploading %s; requeueing' % source)
                self._failures.append({'source': source, 'bucket': bucket, 'target': target})

            if hasattr(e, 'message'):
                if self.isVerbose():
                    print('Error processing %s - %s' % (source, e.message))
                logging.error('Error processing %s - %s' % (source, e.message))
            else:
                if self.isVerbose():
                    print('Error processing %s - %s' % (source, e))
                logging.error('Error processing %s - %s' % (source, e))
            sys.exit(1)

        if not error:
            if self.isVerbose():
                print('Completed %s' % source)
            logging.info('Completed %s' % source)

    def isVerbose(self):
        return self.conf.get('verbose', 'no') == 'yes'

    def _collect_files(self, path, trigger=None):
        path = self.conf.get('source_path')
        bucket = self.conf.get('s3_bucket')
        prefix = self.conf.get('s3_prefix', '')
        result = {1: [], 2: []}   # 1 is files, 2 is triggers

        for root, dirs, files in os.walk(path):
            for name in files:
                file = os.path.join(root, name)[len(path) + 1:]
                item = {'source': os.path.join(path, file), 'bucket': bucket, 'target': os.path.join(prefix, file)}
                if trigger:
                    match = fnmatch.fnmatch(name, trigger)
                    result[int(match) + 1].append(item)
                else:
                    result[1].append(item)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload files concurrently to S3', prog='s3upload')
    parser.add_argument('script', metavar='script', type=argparse.FileType('r'), nargs=1, help='configuration script')
    script = parser.parse_args().script[0]

    config = configparser.ConfigParser()
    config.read_file(script)

    uploader = S3Uploader(config)
    uploader.run()
