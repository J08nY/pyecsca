EC_TESTS = ec.test_context ec.test_configuration ec.test_curve ec.test_formula \
ec.test_params ec.test_key_agreement ec.test_key_generation ec.test_mod ec.test_model \
ec.test_mult ec.test_naf ec.test_op ec.test_point ec.test_signature ec.test_transformations

SCA_TESTS = sca.test_align sca.test_combine sca.test_edit sca.test_filter sca.test_match sca.test_process \
sca.test_sampling sca.test_target sca.test_test sca.test_trace sca.test_traceset sca.test_plot

TESTS = ${EC_TESTS} ${SCA_TESTS}

test:
	nose2 -s test -E "not slow and not disabled" -C -v ${TESTS}

test-plots:
	env PYECSCA_TEST_PLOTS=1 nose2 -s test -E "not slow and not disabled" -C -v ${TESTS}

test-all:
	nose2 -s test -C -v ${TESTS}

typecheck:
	mypy pyecsca --ignore-missing-imports --show-error-codes

codestyle:
	flake8 --ignore=E501,F405,F403,F401,E126 pyecsca

doc-coverage:
	interrogate -vv -nmps pyecsca

docs:
	$(MAKE) -C docs apidoc
	$(MAKE) -C docs html

.PHONY: test test-plots test-all typecheck codestyle doc-coverage docs