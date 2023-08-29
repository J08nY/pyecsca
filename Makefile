EC_TESTS = test.ec.test_context test.ec.test_configuration test.ec.test_curve test.ec.test_formula \
test.ec.test_params test.ec.test_key_agreement test.ec.test_key_generation test.ec.test_mod test.ec.test_model \
test.ec.test_mult test.ec.test_naf test.ec.test_op test.ec.test_point test.ec.test_signature test.ec.test_transformations test.ec.test_regress \
test.ec.test_divpoly

SCA_TESTS = test.sca.test_align test.sca.test_combine test.sca.test_edit test.sca.test_filter test.sca.test_match test.sca.test_process \
test.sca.test_sampling test.sca.test_target test.sca.test_test test.sca.test_trace test.sca.test_traceset test.sca.test_plot test.sca.test_rpa \
test.sca.test_zvp test.sca.test_stacked_combine test.sca.test_leakage_models

TESTS = ${EC_TESTS} ${SCA_TESTS}

PERF_SCRIPTS = test.ec.perf_mod test.ec.perf_formula test.ec.perf_mult test.sca.perf_combine test.sca.perf_zvp

test:
	pytest -m "not slow" --cov=pyecsca

test-plots:
	env PYECSCA_TEST_PLOTS=1 pytest -m "not slow"

test-all:
	pytest --cov=pyecsca

typecheck:
	mypy --namespace-packages -p pyecsca --ignore-missing-imports --show-error-codes --check-untyped-defs

typecheck-all:
	mypy --namespace-packages -p pyecsca -p test --ignore-missing-imports --show-error-codes --check-untyped-defs

codestyle:
	flake8 --extend-ignore=E501,F405,F403,F401,E126,E203 pyecsca

codestyle-all:
	flake8 --extend-ignore=E501,F405,F403,F401,E126,E203 pyecsca test

docstyle:
	pydocstyle pyecsca --ignore=D1,D203,D212 -e --count

black:
	black --exclude pyecsca/ec/{std,efd} pyecsca

black-all:
	black --exclude pyecsca/ec/{std,efd} pyecsca test

perf:
	mkdir -p .perf
	echo ${PERF_SCRIPTS}| env DIR=".perf" xargs -n 1 python -m

perf-plots:
	python test/plots/plot_perf.py -d .perf

doc-coverage:
	interrogate -vv -nmps -e pyecsca/ec/std/.github/ -f 55 pyecsca

docs:
	$(MAKE) -C docs apidoc
	$(MAKE) -C docs html

help:
	@echo "pyecsca, Python Elliptic Curve cryptography Side-Channel Analysis toolkit."
	@echo
	@echo "Available targets:"
	@echo " - test: Test pyecsca."
	@echo " - test-plots: Test pyecsca and produce debugging plots."
	@echo " - test-all: Test pyecsca but also run slow (and disabled) tests."
	@echo " - typecheck: Use mypy to verify the use of types in pyecsca."
	@echo " - typecheck-all: Use mypy to verify the use of types in pyecsca and in tests."
	@echo " - codestyle: Use flake8 to check codestyle in pyecsca."
	@echo " - codestyle-all: Use flake8 to check codestyle in pyecsca and in tests."
	@echo " - docstyle: Use pydocstyle to check format of docstrings."
	@echo " - black: Run black on pyecsca sources (will transform them inplace)."
	@echo " - black-all: Run black on pyecsca sources and tests (will transform them inplace)."
	@echo " - perf: Run performance measurements (prints results and stores them in .perf/)."
	@echo " - perf-plots: Plot performance measurements (stores the plots in .perf/)."
	@echo " - doc-coverage: Use interrogate to check documentation coverage of public API."
	@echo " - docs: Build docs using sphinx."
	@echo " - help: Show this help."

.PHONY: test test-plots test-all typecheck typecheck-all codestyle codestyle-all docstyle black black-all perf doc-coverage docs
