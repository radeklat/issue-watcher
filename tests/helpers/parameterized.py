from parameterized import parameterized


def get_test_case_name_without_index(test_case_func, _param_num, params):
    return f"{test_case_func.__name__}_{parameterized.to_safe_name(params[0][0])}"
