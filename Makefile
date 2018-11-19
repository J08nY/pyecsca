test:
	nose2 -A !slow -v

test-plots:
	env PYECSCA_TEST_PLOTS=1 nose2 -A !slow -v

test-all:
	nose2 -v

.PHONY: test test-plots test-all