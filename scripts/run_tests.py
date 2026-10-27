"""Execute Django tests and retain per-test results for the submission workbook."""
import os
import sys
import json
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.test.runner import DiscoverRunner

class Result(unittest.TextTestResult):
    records = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'test':test.id(),'status':'PASS','actual':'All assertions passed.'})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({'test':test.id(),'status':'FAIL','actual':self._exc_info_to_string(err,test)})
    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({'test':test.id(),'status':'ERROR','actual':self._exc_info_to_string(err,test)})

class Runner(DiscoverRunner):
    def __init__(self, *args, stream=None, **kwargs):
        self.evidence_stream = stream
        super().__init__(*args, **kwargs)
    def get_test_runner_kwargs(self):
        kwargs = super().get_test_runner_kwargs()
        kwargs['stream'] = self.evidence_stream
        return kwargs
    def get_resultclass(self):
        return Result

if __name__ == '__main__':
    root=Path(__file__).resolve().parent.parent
    evidence=root/'submission'/'03_Marketplace'/'evidence'
    evidence.mkdir(parents=True,exist_ok=True)
    with (evidence/'test-output.txt').open('w',encoding='utf-8') as output:
        failures=Runner(verbosity=2,stream=output).run_tests(['marketplace'])
    (evidence/'test-results.json').write_text(json.dumps({'database':django.conf.settings.DATABASES['default']['ENGINE'],'results':Result.records},indent=2),encoding='utf-8')
    print(f'{len(Result.records)} tests executed; {failures} failures. Evidence: {evidence}')
    sys.exit(bool(failures))
