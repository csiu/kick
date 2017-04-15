dirs = data
dirs += results
dirs += src/python

.PHONY: directories

all: directories
directories: $(dirs)
$(dirs):
	mkdir -p $@

# Download data ----------------------------------------------------------------
# Download CSV data set from https://webrobots.io/kickstarter-datasets/
data/01_data_set:
	python src/python/01_download.py $@

# Load data to PostgreSQL
#python src/python/02_load.py /Users/csiu/repo/kick/data/01_data_set
