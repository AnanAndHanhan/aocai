import argparse
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('maintenance',Path(__file__).parents[1]/'scripts/maintenance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(period=191):
    nums=[19,43,39,24,16,26,29]
    return {'expect':f'2026{period:03}','openTime':'2026-07-10 21:32:32','type':'8',
            'openCode':','.join(f'{x:02}' for x in nums),'zodiac':','.join(m.zodiac(x) for x in nums)}


def payload(*rows):return {'result':True,'code':200,'data':list(rows)}


class HistoryTests(unittest.TestCase):
    def test_order_and_special_are_preserved(self):
        row=m.normalize_history(payload(fixture()),2026)[0]
        self.assertEqual(row['first_number'],19)
        self.assertEqual(row['special_number'],29)
        self.assertEqual(row['regular_numbers'],[19,43,39,24,16,26])
        self.assertEqual(row['special_zodiac'],'虎')

    def test_identical_duplicates_are_collapsed(self):
        self.assertEqual(len(m.normalize_history(payload(fixture(),fixture()),2026)),1)

    def test_conflicting_duplicate_is_rejected(self):
        bad=fixture();bad['openTime']='2026-07-11 21:32:32'
        with self.assertRaisesRegex(ValueError,'重复记录冲突'):m.normalize_history(payload(fixture(),bad),2026)

    def test_wrong_lottery_is_rejected(self):
        row=fixture();row['type']='7'
        with self.assertRaises(ValueError):m.normalize_history(payload(row),2026)

    def test_duplicate_number_is_rejected(self):
        row=fixture();row['openCode']='19,19,39,24,16,26,29'
        with self.assertRaises(ValueError):m.normalize_history(payload(row),2026)

    def test_wrong_zodiac_is_rejected(self):
        row=fixture();row['zodiac']='牛,鼠,龙,羊,兔,蛇,虎'
        with self.assertRaisesRegex(ValueError,'生肖'):m.normalize_history(payload(row),2026)

    def test_unknown_year_mapping_is_rejected(self):
        with self.assertRaises(ValueError):m.normalize_history(payload(fixture()),2027)

    def test_only_confirmed_range_is_imported(self):
        old=fixture(47);old['zodiac']='旧映射'
        self.assertEqual(len(m.normalize_history(payload(old,fixture()),2026)),1)

    def test_missing_window_does_not_make_statistics(self):
        rows=[{'period':i,'special_zodiac':'狗'} for i in range(141,191) if i!=170]
        self.assertEqual(m.windows(rows)['50']['status'],'缺期，不生成频次')

    def test_counts_only_special(self):
        rows=[{'period':i,'special_zodiac':'狗','first_zodiac':'牛','numbers':[6]*7} for i in range(141,191)]
        stats=m.windows(rows)
        self.assertEqual(stats['50']['special_zodiac_counts']['狗'],50)
        self.assertEqual(stats['50']['special_zodiac_counts']['牛'],0)
        self.assertEqual(sum(stats['30']['special_zodiac_counts'].values()),30)

    def test_result_conflict_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            root=Path(tmp);source=root/'input.json';source.write_text(json.dumps(payload(fixture())))
            p=root/'每期归档/2026/191';p.mkdir(parents=True)
            (p/'开奖结果.json').write_text(json.dumps({'regular_numbers':[1,2,3,4,5,6],'special_number':7}))
            with self.assertRaisesRegex(ValueError,'结果冲突'):
                m.sync_history(argparse.Namespace(input=str(source),year=2026,archive_from=191))
            self.assertFalse((root/'数据').exists())

    def test_freeze_is_immutable_and_does_not_claim_pre_draw(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            p=Path(tmp)/'每期归档/2026/304';p.mkdir(parents=True)
            (p/'分析-v001.md').write_text('original')
            version={'version':'v001','analysis_file':'分析-v001.md','main':list('牛兔龙鼠马猴'),'defense':list('猪蛇鸡')}
            (p/'预测记录.json').write_text(json.dumps({'versions':[version]}))
            args=argparse.Namespace(year=2026,period=304,version='v001')
            m.freeze(args)
            (p/'分析-v001.md').write_text('changed later')
            self.assertEqual((p/'冻结记录/v001/分析.md').read_text(),'original')
            receipt=json.loads((p/'冻结记录/v001/凭据.json').read_text())
            self.assertFalse(receipt['pre_draw_proven'])
            with self.assertRaisesRegex(ValueError,'已冻结'):m.freeze(args)

if __name__=='__main__':unittest.main()
