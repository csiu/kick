dirs = data
dirs += results
dirs += src/python

.PHONY: directories

all: directories
directories: $(dirs)
$(dirs):
	mkdir -p $@
