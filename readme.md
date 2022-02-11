# Installation

Create the virtual environment with:
~~~
python3 -m venv venv
~~~

Activate the virtual environment with:
~~~
source venv/bin/activate
~~~

Install the dependencies with:
~~~
pip install -r requirements.txt
~~~

# Operation

Call the shell script `s3upload` with the script name:
~~~
/path/to/s3upload /path/to/your/script/file.conf
~~~

# Sample Script File

~~~
[config]
aws_access_key      = **********
aws_secret_key      = ********************
aws_region_name     = eu-west-1

s3_bucket           = mybucket
s3_prefix           = testing/s3uploads

source_path         = /path/to/local/files
num_threads         = 10
log_file            = /path/to/local/logfile.log
log_level           = debug
trigger             = *xml
verbose             = yes

multipart_threshold = 8388608
max_concurrency     = 20
multipart_chunksize = 8388608
max_io_queue        = 100
io_chunksize        = 262144
~~~

The `[config]` section controls how the s3 uploader works and should be fairly
obvious:

* `aws_access_key`  - The AWS access key ID
* `aws_secret_key`  - The AWS secret key
* `aws_region_name` - The target AWS region 
* `s3_bucket` - The target bucket name
* `s3_prefix` - (optional) the prefix (or target path) for the uploaded files
* `source_path` - the base on the local system for all the files
* `num_threads` - (optional) controls the maximum number of concurrent uploads
* `log_file` - (optional) the log file name
* `log_level` - (optional) the logging level (debug, info, warn, error) `[OPTIONAL]`
* `trigger` - (optional) the wildcard specification for the trigger files
* `verbose` - (optional) defaults to 'no' - if 'yes' will print messages to stdout
* `multipart_threshold` - (optional) The transfer size threshold for which multipart uploads, downloads, and copies will automatically be triggered.
* `max_concurrency` - (optional) The maximum number of fibers that will be making requests to perform a transfer.
* `multipart_chunksize` - (optional) The partition size of each part for a multipart transfer.
* `max_io_queue` - (optional) The maximum amount of read parts that can be queued in memory to be written for a download. The size of each of these read parts is at most the size of io_chunksize.
* `io_chunksize` - (optional) The max size of each chunk in the io queue. Currently, this is size used when read is called on the downloaded stream as well.

Files will be uploaded in order:

* excluding the trigger files
* then and only then then, just the trigger files

The default values are:
* aws_region_name `<empty>`
* s3_prefix `<empty>`
* num_threads `10`
* log_file `None`
* log_level `info`
* trigger `<empty>`
* verbose `no`
* multipart_threshold `8388608`
* max_concurrency `10`
* multipart_chunksize `8388608`
* max_io_queue `100`
* io_chunksize `262144`

If no trigger specification is set, then s3upload will simply upload the contents of the folder in whatever order it sees fit, 
