from oort.shared.utils import find_first_in_list


def test_find_item_in_valid_list():
    calibrations = [{'uuid': '1', 'name': 'Biases', 'datasets': '10'},
                    {'uuid': '2', 'name': 'Biases', 'datasets': '20'}]
    assert (find_first_in_list(calibrations, name='Biases', uuid='2') == calibrations[1])


def test_find_observation_skipping_name_success():
    observations = [{'uuid': '38c1391f-f8a4-4000-b688-e5bc12a3b463', 'index': 0,
                     'night_log': '07dd5758-cebe-46fb-a888-2fb068747a51', 'target_name': '',
                     'target_class': 'AstronomicalObject',
                     'dataset': 'b4bbd718-93b6-4efe-8aa6-69c6be9e8845'}]

    kwargs = {'name': '[HD 5980] V', 'night_log': '07dd5758-cebe-46fb-a888-2fb068747a51'}

    # Name is not being part of the keys of the observation and must not be used in filtering.
    # However, if name is skipped, one must ensure tests is still effective, that is,
    # remaining provided keys in kwargs are enough to get a meaning ful result.
    assert (find_first_in_list(observations, **kwargs) == observations[0])


def test_find_observation_skipping_keys_failure():
    observations = [{'uuid': '38c1391f-f8a4-4000-b688-e5bc12a3b463', 'index': 0,
                     'night_log': '07dd5758-cebe-46fb-a888-2fb068747a51', 'target_name': '',
                     'target_class': 'AstronomicalObject',
                     'dataset': 'b4bbd718-93b6-4efe-8aa6-69c6be9e8845'}]

    kwargs = {'name': '[HD 5980] V'}
    # Name will be skipped because it doesn't exists in observation. But no keys are left
    # for comparison, hence the result must be None.
    assert find_first_in_list(observations, **kwargs) is None
