#!/usr/bin/env python3
"""澳彩资料维护工具。仅核验/归档，不执行预测或自动改写冻结分析。"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = dt.timezone(dt.timedelta(hours=8))
SOURCE = 'https://history.macaumarksix.com/history/macaujc2/y/{year}'
ZODIACS = '马蛇龙兔虎牛鼠猪狗鸡猴羊'
TRAD = str.maketrans('馬雞龍豬', '马鸡龙猪')


def now():
    return dt.datetime.now(TZ).isoformat(timespec='seconds')


def zodiac(number):
    if not 1 <= number <= 49:
        raise ValueError('号码不在1—49')
    return ZODIACS[(number - 1) % 12]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_history(payload, year, min_period=141):
    if payload.get('result') is not True or payload.get('code') != 200:
        raise ValueError('来源响应失败')
    if year != 2026:
        raise ValueError('当前号码生肖表仅确认2026年，其他年份需先更新映射')
    unique = {}
    for row in payload['data']:
        expect = str(row['expect'])
        if str(row.get('type')) != '8' or not re.fullmatch(r'\d{7}', expect) or int(expect[:4]) != year:
            raise ValueError('彩种或年份/期号不符')
        period = int(expect[4:])
        if not 1 <= period <= 366:
            raise ValueError('期号越界')
        if period < min_period:
            continue  # 本库既有范围141起；更早年份/农历映射需单独确认
        numbers = [int(n) for n in row['openCode'].split(',')]
        if len(numbers) != 7 or len(set(numbers)) != 7:
            raise ValueError(f'{period}期号码不足或重复')
        zs = [zodiac(n) for n in numbers]
        source_zs = row.get('zodiac', '').translate(TRAD).split(',')
        if zs != source_zs:
            raise ValueError(f'{period}期来源生肖与基础映射冲突')
        date = dt.datetime.strptime(row['openTime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ)
        if date.year != year or date > dt.datetime.now(TZ):
            raise ValueError('开奖日期年份不符或未来开奖')
        item = dict(year=year, period=period, lottery='新澳门六合彩',
                    draw_time=date.isoformat(), numbers=numbers, zodiacs=zs,
                    regular_numbers=numbers[:6], special_number=numbers[-1],
                    first_number=numbers[0], first_zodiac=zs[0], special_zodiac=zs[-1])
        if period in unique and unique[period] != item:
            raise ValueError(f'{period}期重复记录冲突，拒绝覆盖')
        unique[period] = item
    if not unique:
        raise ValueError('来源无结果')
    return [unique[p] for p in sorted(unique)]


def windows(records):
    ordered = sorted(records, key=lambda x: x['period'])
    stats = {}
    for size in (30, 50):
        block = ordered[-size:]
        contiguous = len(block) == size and [x['period'] for x in block] == list(range(block[-1]['period']-size+1, block[-1]['period']+1))
        if not contiguous:
            stats[str(size)] = {'status': '缺期，不生成频次'}
            continue
        counts = collections.Counter(x['special_zodiac'] for x in block)
        stats[str(size)] = {'status': '完整', 'start': block[0]['period'], 'end': block[-1]['period'],
                            'special_zodiac_counts': {z: counts[z] for z in '鼠牛虎兔龙蛇马羊猴鸡狗猪'}}
    return stats


def sync_history(args):
    if args.input:
        raw = Path(args.input).read_bytes()
    else:
        raw = subprocess.check_output(['curl', '-fLsS', '--max-time', '30', SOURCE.format(year=args.year)])
    records = normalize_history(json.loads(raw), args.year)
    target = ROOT / f'数据/开奖记录-{args.year}.json'
    old = json.loads(target.read_text())['records'] if target.exists() else []
    oldmap = {x['period']: x for x in old}
    if old and records[-1]['period'] < old[-1]['period']:
        raise ValueError('接口最新期落后本地，拒绝旧响应')
    for row in records:
        if row['period'] in oldmap and oldmap[row['period']] != row:
            raise ValueError(f"已保存{row['period']}期与接口冲突，需人工核验")
    if records == old:
        print('开奖无变化，不改归档或重复生成复盘')
        return
    merged = {**oldmap, **{x['period']: x for x in records}}
    records = [merged[p] for p in sorted(merged)]
    # 所有已有逐期结果先校验，校验失败时不写任何归档。
    for row in records:
        result_file = ROOT / f"每期归档/{args.year}/{row['period']}/开奖结果.json"
        if result_file.exists():
            prior = json.loads(result_file.read_text())
            if prior.get('special_number') is not None and (prior.get('regular_numbers') != row['regular_numbers'] or prior.get('special_number') != row['special_number']):
                raise ValueError(f"第{row['period']}期既有结果冲突")
    seq = [row['period'] for row in records]
    if seq != list(range(seq[0], seq[-1]+1)):
        raise ValueError('待写入历史有缺期，停止导入')
    stamp = now()
    digest = hashlib.sha256(raw).hexdigest()
    evidence = ROOT / f'数据/来源/{args.year}-{digest[:12]}.json'
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(raw)
    dump(target, {'source_page': 'https://macaujc.com/', 'source': SOURCE.format(year=args.year),
                  'fetched_at': stamp, 'source_file': str(evidence.relative_to(ROOT)),
                  'source_sha256': digest, 'records': records})
    dump(ROOT / f'数据/特码统计-{args.year}.json', windows(records))
    for row in records:
        if row['period'] < args.archive_from or row['period'] in oldmap:
            continue
        p = ROOT / f"每期归档/{args.year}/{row['period']}"
        result = p / '开奖结果.json'
        if result.exists():
            existing = json.loads(result.read_text())
            if existing.get('special_number') is not None and (existing.get('regular_numbers') != row['regular_numbers'] or existing.get('special_number') != row['special_number']):
                raise ValueError('逐期归档与历史接口冲突')
        if not result.exists() or json.loads(result.read_text()).get('special_number') is None:
            dump(result, {**row, 'source': SOURCE.format(year=args.year), 'fetched_at': stamp,
                          'source_file': str(evidence.relative_to(ROOT))})
        md = p / '开奖结果.md'
        if not md.exists():
            md.write_text(f"# {args.year}年第{row['period']}期新澳门六合彩\n\n开奖：{row['draw_time']}\n\n正码：" +
                          '、'.join(f'{n:02}{zodiac(n)}' for n in row['regular_numbers']) +
                          f"\n\n特码：{row['special_number']:02}{row['special_zodiac']}；首号：{row['first_number']:02}{row['first_zodiac']}。\n\n来源及原始响应索引见开奖结果.json。\n")
        review = p / '复盘.md'
        if not review.exists():
            review.write_text(f"# 第{row['period']}期补录复盘\n\n本次补录仅有实际结果，未归档当期资料或预测。无法分析资料遗漏、计算预测成绩，待用户补充原始资料。不得依据开奖号重建所谓开奖前预测。\n")
        readme = p / 'README.md'
        if not readme.exists():
            readme.write_text(f"# {args.year}年第{row['period']}期\n\n- [实际结果](开奖结果.md)\n- [无资料复盘说明](复盘.md)\n\n状态：仅历史开奖补录，无资料、无预测。\n")
    lines = ['# 开奖记录', '', '彩种：新澳门六合彩。当前来源为用户指定站点实际引用接口；旧来源快照见历史文档。',
             '', f'数据截至{args.year}年第{records[-1]["period"]}期。原始响应、抓取时间和去重后数据见数据目录。',
             '', '## 近30/50期统计（仅特码）', '']
    for size, info in windows(records).items():
        if info['status'] != '完整':
            lines += [f'- 近{size}期：缺期，不生成统计。']
        else:
            lines += [f"- 近{size}期（{info['start']}—{info['end']}）：" +
                      '、'.join(f'{z}{n}次' for z,n in info['special_zodiac_counts'].items())]
    lines += ['', '## 明细', '', '| 期数 | 日期 | 六码正码（顺序不变） | 特码 | 首号 |', '| --- | --- | --- | --- | --- |']
    for row in records:
        regular = ' '.join(f'{n:02}{zodiac(n)}' for n in row['regular_numbers'])
        lines.append(f"| {row['period']} | {row['draw_time'][:10]} | {regular} | {row['special_number']:02}{row['special_zodiac']} | {row['first_number']:02}{row['first_zodiac']} |")
    (ROOT / '开奖记录.md').write_text('\n'.join(lines)+'\n')
    idx = ['# 每期归档索引', '', '| 年份 | 期号 | 状态 |', '| --- | --- | --- |']
    for p in sorted((ROOT/'每期归档'/str(args.year)).iterdir(), key=lambda p:int(p.name)):
        if p.is_dir():
            state = '资料分析及结果已保存' if (p/'预测记录.json').exists() else '仅历史结果，无预测'
            idx.append(f'| {args.year} | [{p.name}]({args.year}/{p.name}/README.md) | {state} |')
    (ROOT/'每期归档/README.md').write_text('\n'.join(idx)+'\n')
    print(f'保存{len(records)}条唯一期记录，最新{records[-1]["period"]}；生成近30/50期仅特码统计。')


def init_period(args):
    p = ROOT / f'每期归档/{args.year}/{args.period}'
    p.mkdir(parents=True, exist_ok=True)
    (p/'原始资料').mkdir(exist_ok=True)
    file = p/'资料检查.json'
    if file.exists():
        raise ValueError('已有检查表，拒绝覆盖')
    dump(file, {'year':args.year, 'period':args.period, 'created_at':now(),
                'expected_materials':[], 'received_files':[], 'missing_materials':[],
                'scope_confirmed':False, 'ambiguous_text':[], 'previous_first_verified':False,
                'downgrades_checked':False, 'status':'暂定，待核对资料齐全及范围'})
    (p/'时间记录.jsonl').open('a').write(json.dumps({'event':'period_created','at':now()},ensure_ascii=False)+'\n')
    with (p/'证据表.csv').open('x', newline='') as f:
        csv.writer(f, lineterminator="\n").writerow(['证据ID','资料文件','原句','有效区域','规则ID或基础表','分类/外号','候选生肖','号码','证据强弱','同源组','独立交叉','降权','排序理由','发现阶段','关联版本'])
    print(p)


def freeze(args):
    p = ROOT / f'每期归档/{args.year}/{args.period}'
    prediction = json.loads((p/'预测记录.json').read_text())
    v = next(x for x in prediction['versions'] if x['version']==args.version)
    if not v.get('main') or len(v['main']) != 6 or len(v.get('defense',[])) != 3 or len(set(v['main']+v['defense'])) != 9:
        raise ValueError('必须为不重复的主6防3完整预测')
    if v.get('status') == 'final':
        intake = json.loads((p/'资料检查.json').read_text())
        if intake.get('missing_materials') or not all(intake.get(k) for k in ('scope_confirmed','previous_first_verified','downgrades_checked')):
            raise ValueError('资料或范围/首号/降权未确认，不能冻结最终版；请标暂定')
        if not v.get('formed_at'):
            raise ValueError('最终版必须保存实际形成时间，不可倒填')
    base = p/'冻结记录'/args.version
    if base.exists():
        raise ValueError('版本已冻结，拒绝覆盖，请新建版本')
    analysis = p/v['analysis_file']
    content = analysis.read_bytes()
    base.mkdir(parents=True)
    (base/'分析.md').write_bytes(content)
    dump(base/'预测.json',v)
    stamp = now()
    actual_time = None
    if (p/'开奖结果.json').exists():
        actual_time = json.loads((p/'开奖结果.json').read_text()).get('draw_time')
    # 冻结时钟本身不能证明历史分析何时形成；当前快照只证明此刻存在。
    dump(base/'凭据.json', {'version':args.version,'snapshot_created_at':stamp,
                           'historical_formed_at':v.get('formed_at'),
                           'analysis_sha256':hashlib.sha256(content).hexdigest(),
                           'prediction_sha256':sha(base/'预测.json'), 'known_draw_time':actual_time,
                           'pre_draw_proven':False,
                           'note':'若要认证开奖前版本，须有开奖前远程提交及原始时间记录独立核验；不可倒填'})
    print('快照已冻结；不据当前时间认证历史预测成绩')


def audit(_args):
    issues=[]
    for p in (ROOT/'每期归档').glob('*/*'):
        if not p.is_dir(): continue
        for f in p.glob('*.json'):
            try: json.loads(f.read_text())
            except Exception as e: issues.append(f'{f}: {e}')
        metadata=p/'归档信息.json'
        if metadata.exists():
            for row in json.loads(metadata.read_text()).get('files',[]):
                file=p/row['path']
                if not file.exists() or sha(file)!=row['sha256']: issues.append(f'原图缺失或哈希不符: {file}')
        for rec in (p/'冻结记录').glob('*/凭据.json'):
            v=json.loads(rec.read_text());base=rec.parent
            if sha(base/'分析.md')!=v['analysis_sha256'] or sha(base/'预测.json')!=v['prediction_sha256']:
                issues.append(f'冻结快照变动: {base}')
        result=p/'开奖结果.json'
        if result.exists():
            d=json.loads(result.read_text())
            if d.get('special_number') is not None:
                nums=d['regular_numbers']+[d['special_number']]
                if len(nums)!=7 or len(set(nums))!=7:issues.append(f'结果号码异常: {p}')
                if d.get('first_number')!=nums[0] or d.get('first_zodiac')!=zodiac(nums[0]) or d.get('special_zodiac')!=zodiac(nums[-1]):issues.append(f'首号/特码映射异常: {p}')
    for file in (ROOT/'数据').glob('开奖记录-*.json'):
        d=json.loads(file.read_text());seq=[x['period'] for x in d['records']]
        if seq!=list(range(min(seq),max(seq)+1)):issues.append(f'缺期: {file}')
        source=ROOT/d['source_file']
        if not source.exists() or sha(source)!=d['source_sha256']:issues.append(f'来源证据异常: {file}')
    if issues: raise ValueError('\n'.join(issues))
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    print('归档JSON、原图哈希、冻结快照、号码、生肖、缺期与空白检查通过')


def health(_args):
    local = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    remote_line = subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).strip()
    if not remote_line:
        raise ValueError('远程main不存在或不可读')
    remote = remote_line.split()[0]
    dirty = subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    print(json.dumps({'local_head':local,'remote_main':remote,'synced':local==remote,
                      'working_tree_clean':not bool(dirty)},ensure_ascii=False))
    if local != remote or dirty:
        raise ValueError('有未提交或未同步变更，完成维护后再核验，不能报上传成功')


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    s=sub.add_parser('sync-history');s.add_argument('--year',type=int,default=2026);s.add_argument('--input');s.add_argument('--archive-from',type=int,default=191);s.set_defaults(run=sync_history)
    s=sub.add_parser('init-period');s.add_argument('period',type=int);s.add_argument('--year',type=int,default=2026);s.set_defaults(run=init_period)
    s=sub.add_parser('freeze');s.add_argument('period',type=int);s.add_argument('version');s.add_argument('--year',type=int,default=2026);s.set_defaults(run=freeze)
    s=sub.add_parser('audit');s.set_defaults(run=audit)
    s=sub.add_parser('health');s.set_defaults(run=health)
    args=ap.parse_args()
    try: args.run(args)
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as e:
        ap.exit(1, f'维护失败：{e}\n')

if __name__=='__main__':main()
