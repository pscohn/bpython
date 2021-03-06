from bpython import autocomplete

import mock
try:
    import unittest2 as unittest
except ImportError:
    import unittest

#TODO: Parts of autocompletion to test:
# Test that the right matches come back from find_matches (test that priority is correct)
# Test the various complete methods (import, filename) to see if right matches
# Test that MatchesIterator.substitute correctly subs given a match and a completer

class TestSafeEval(unittest.TestCase):
    def test_catches_syntax_error(self):
        self.assertRaises(autocomplete.EvaluationError,
                          autocomplete.safe_eval, '1re', {})


class TestFormatters(unittest.TestCase):

    def test_filename(self):
        last_part_of_filename = autocomplete.FilenameCompletion.format
        self.assertEqual(last_part_of_filename('abc'), 'abc')
        self.assertEqual(last_part_of_filename('abc/'), 'abc/')
        self.assertEqual(last_part_of_filename('abc/efg'), 'efg')
        self.assertEqual(last_part_of_filename('abc/efg/'), 'efg/')
        self.assertEqual(last_part_of_filename('/abc'), 'abc')
        self.assertEqual(last_part_of_filename('ab.c/e.f.g/'), 'e.f.g/')

    def test_attribute(self):
        self.assertEqual(autocomplete.after_last_dot('abc.edf'), 'edf')

def completer(matches):
    mock_completer = autocomplete.BaseCompletionType()
    mock_completer.matches = mock.Mock(return_value=matches)
    return mock_completer

class TestGetCompleter(unittest.TestCase):

    def test_no_completers(self):
        self.assertTupleEqual(autocomplete.get_completer([], 0, ''), ([], None))

    def test_one_completer_without_matches_returns_empty_list_and_none(self):
        a = completer([])
        self.assertTupleEqual(autocomplete.get_completer([a], 0, ''), ([], None))

    def test_one_completer_returns_matches_and_completer(self):
        a = completer(['a'])
        self.assertTupleEqual(autocomplete.get_completer([a], 0, ''), (['a'], a))

    def test_two_completers_with_matches_returns_first_matches(self):
        a = completer(['a'])
        b = completer(['b'])
        self.assertEqual(autocomplete.get_completer([a, b], 0, ''), (['a'], a))

    def test_first_non_none_completer_matches_are_returned(self):
        a = completer([])
        b = completer(['a'])
        self.assertEqual(autocomplete.get_completer([a, b], 0, ''), ([], None))

    def test_only_completer_returns_None(self):
        a = completer(None)
        self.assertEqual(autocomplete.get_completer([a], 0, ''), ([], None))

    def test_first_completer_returns_None(self):
        a = completer(None)
        b = completer(['a'])
        self.assertEqual(autocomplete.get_completer([a, b], 0, ''), (['a'], b))

class TestCumulativeCompleter(unittest.TestCase):

    def completer(self, matches, ):
        mock_completer = autocomplete.BaseCompletionType()
        mock_completer.matches = mock.Mock(return_value=matches)
        return mock_completer

    def test_no_completers_fails(self):
        with self.assertRaises(ValueError):
            autocomplete.CumulativeCompleter([])

    def test_one_empty_completer_returns_empty(self):
        a = self.completer([])
        cumulative = autocomplete.CumulativeCompleter([a])
        self.assertEqual(cumulative.matches(3, 'abc', 1, 1, 1, 1), [])

    def test_one_none_completer_returns_empty(self):
        a = self.completer(None)
        cumulative = autocomplete.CumulativeCompleter([a])
        self.assertEqual(cumulative.matches(3, 'abc', 1, 1, 1, 1), [])

    def test_two_completers_get_both(self):
        a = self.completer(['a'])
        b = self.completer(['b'])
        cumulative = autocomplete.CumulativeCompleter([a, b])
        self.assertEqual(cumulative.matches(3, 'abc', 1, 1, 1, 1), (['a', 'b']))


class TestFilenameCompletion(unittest.TestCase):

    def test_locate_fails_when_not_in_string(self):
        self.assertEqual(autocomplete.FilenameCompletion.locate(4, "abcd"), None)

    def test_locate_succeeds_when_in_string(self):
        self.assertEqual(autocomplete.FilenameCompletion.locate(4, "a'bc'd"), (2, 4, 'bc'))

    @mock.patch('bpython.autocomplete.glob', new=lambda text: [])
    def test_match_returns_none_if_not_in_string(self):
        self.assertEqual(autocomplete.FilenameCompletion.matches(2, 'abcd'), None)

    @mock.patch('bpython.autocomplete.glob', new=lambda text: [])
    def test_match_returns_empty_list_when_no_files(self):
        self.assertEqual(autocomplete.FilenameCompletion.matches(2, '"a'), [])

    @mock.patch('bpython.autocomplete.glob', new=lambda text: ['abcde', 'aaaaa'])
    @mock.patch('os.path.expanduser', new=lambda text: text)
    @mock.patch('os.path.isdir', new=lambda text: False)
    @mock.patch('os.path.sep', new='/')
    def test_match_returns_files_when_files_exist(self):
        self.assertEqual(autocomplete.FilenameCompletion.matches(2, '"x'), ['abcde', 'aaaaa'])

    @mock.patch('bpython.autocomplete.glob', new=lambda text: ['abcde', 'aaaaa'])
    @mock.patch('os.path.expanduser', new=lambda text: text)
    @mock.patch('os.path.isdir', new=lambda text: True)
    @mock.patch('os.path.sep', new='/')
    def test_match_returns_dirs_when_dirs_exist(self):
        self.assertEqual(autocomplete.FilenameCompletion.matches(2, '"x'), ['abcde/', 'aaaaa/'])

    @mock.patch('bpython.autocomplete.glob', new=lambda text: ['/expand/ed/abcde', '/expand/ed/aaaaa'])
    @mock.patch('os.path.expanduser', new=lambda text: text.replace('~', '/expand/ed'))
    @mock.patch('os.path.isdir', new=lambda text: False)
    @mock.patch('os.path.sep', new='/')
    def test_tilde_stays_pretty(self):
        self.assertEqual(autocomplete.FilenameCompletion.matches(4, '"~/a'), ['~/abcde', '~/aaaaa'])

    @mock.patch('os.path.sep', new='/')
    def test_formatting_takes_just_last_part(self):
        self.assertEqual(autocomplete.FilenameCompletion.format('/hello/there/'), 'there/')
        self.assertEqual(autocomplete.FilenameCompletion.format('/hello/there'), 'there')
