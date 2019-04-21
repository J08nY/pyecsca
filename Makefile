test:
	nose2 -A !slow -C -v

test-plots:
	env PYECSCA_TEST_PLOTS=1 nose2 -A !slow -C -v

test-all:
	nose2 -C -v

typecheck:
	mypy -p pyecsca --ignore-missing-imports

.PHONY: test test-plots test-all typecheck