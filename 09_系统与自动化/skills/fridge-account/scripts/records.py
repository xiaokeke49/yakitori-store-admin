#!/usr/bin/env python3
"""Local Markdown records only. Never logs into or publishes to a platform."""
import argparse
import hashlib
import html
import json
import math
import re
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4] / '06_公域运营/产品展示冰箱'
TABLES = {
 'metrics': ('后台数据.md', ['账号','作品','采集时间','统计区间','指标','口径','值','单位','证据'], list(range(6))),
 'peers': ('同行研究.md', ['账号','作品','观察时间','平台评论','顾客评论','正向兴趣评论','完整核实','冰箱相关','证据','对照作品','结论'], [0,1,2]),
 'published': ('小红书发布记录.md', ['时间','链接','版本','成片SHA256','原图SHA256','成功证据'], [1]),
 'assets': ('../../09_系统与自动化/skills/fridge-account/data/素材登记.md', ['SHA256','文件','用途','版本','原图SHA256','验收','说明'], [0]),
}

def timestamp(v):
    d = datetime.fromisoformat(v)
    if d.tzinfo is None:
        raise ValueError('时间必须含时区，如 2026-09-09T10:00:00+08:00')
    return d.isoformat()

def number(v):
    if v is None or v == '缺失': return '缺失'
    if isinstance(v, bool): raise ValueError('布尔值不是指标')
    n = float(v)
    if not math.isfinite(n) or n < 0: raise ValueError('指标必须为非负有限数或 null')
    return str(int(n)) if n.is_integer() else str(n)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def encode(v):
    return html.escape(str(v), quote=False).replace('|','&#124;').replace('\n','&#10;')

def read_table(path):
    if not path.exists(): return []
    s=path.read_text()
    if '<!-- records:start -->' not in s: return []
    block=s.split('<!-- records:start -->',1)[1].split('<!-- records:end -->',1)[0]
    return [[html.unescape(c.strip()) for c in line.strip().strip('|').split('|')] for line in block.splitlines() if line.startswith('|')][2:]

def append(project, kind, row):
    filename, columns, keys = TABLES[kind]
    path=project/filename
    rows=read_table(path)
    for old in rows:
        if [old[i] for i in keys] == [row[i] for i in keys]:
            if old==row: return '已存在，跳过'
            raise ValueError('同一记录已有不同数据；不覆盖，请保留原证据并另记采集时间/版本')
    rows.append(row)
    block='<!-- records:start -->\n| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'
    block+=''.join('| '+' | '.join(encode(c) for c in r)+' |\n' for r in rows)+'<!-- records:end -->'
    s=path.read_text() if path.exists() else '# '+path.stem+'\n\n'
    if '<!-- records:start -->' in s:
        s=s.split('<!-- records:start -->',1)[0]+block+s.split('<!-- records:end -->',1)[1]
    else: s+=block+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.md.tmp')
    temp.write_text(s); temp.replace(path)
    return '已记录'

def ingest(project, kind, d):
    if kind=='metrics':
        if d['口径'] not in ('累计','区间','时点'): raise ValueError('口径须为累计/区间/时点')
        d['采集时间']=timestamp(d['采集时间']);d['值']=number(d.get('值'))
    elif kind=='peers':
        d['观察时间']=timestamp(d['观察时间'])
        for field in ('平台评论','顾客评论','正向兴趣评论'):
            value=number(d.get(field))
            if value!='缺失' and '.' in value: raise ValueError('评论数必须为整数')
            d[field]=value
        for field in ('完整核实','冰箱相关'):
            if d[field] not in ('是','否','未知'): raise ValueError('核实字段须为是/否/未知')
        counts=[d[x] for x in ('平台评论','顾客评论','正向兴趣评论')]
        if '缺失' not in counts:
            total, customers, interested=map(int,counts)
            if not 0<=interested<=customers<=total: raise ValueError('评论分子分母不一致')
            qualified=total>=20 and customers>0 and interested * 10 >= customers * 3
        else: qualified=False
        qualified=qualified and d['完整核实']=='是' and d['冰箱相关']=='是' and bool(d.get('证据')) and bool(d.get('对照作品'))
        d['结论']='合格' if qualified else '候选/不满足'
    elif kind=='published':
        d['时间']=timestamp(d['时间'])
        if not d['链接'].startswith('https://'): raise ValueError('必须提供真实发布链接')
        for old in read_table(project/TABLES['published'][0]):
            if old[1]==d['链接']:
                row=[str(d.get(c,'')) for c in TABLES['published'][1]]
                if old==row: return '已存在，跳过'
                raise ValueError('同一发布链接已有不同记录，未覆盖')
        rows=read_table(project/TABLES['assets'][0])
        by_hash={r[0]:r for r in rows}
        hashes=d['成片SHA256'].split(',')
        for h in hashes:
            if h not in by_hash: raise ValueError('成片未登记')
        check_package(project,[by_hash[h][1] for h in hashes])
        expected=set(','.join(by_hash[h][4] for h in hashes).split(','))
        if set(d['原图SHA256'].split(','))!=expected: raise ValueError('发布记录原图与台账不一致')
    elif kind=='assets':
        path=Path(d['文件'])
        if not path.is_absolute(): path=project/path
        d['SHA256']=sha(path)
        if d['用途'] not in ('策划示意','同行参考','发布候选','自家原图'): raise ValueError('用途无效')
        if d['验收'] not in ('待核实','通过','已发布'): raise ValueError('验收状态无效')
        if d['用途']!='发布候选' and d['验收']=='已发布': raise ValueError('仅发布候选可标记已发布')
        hashes=d.get('原图SHA256','')
        if hashes and any(not re.fullmatch('[0-9a-f]{64}',h) for h in hashes.split(',')): raise ValueError('原图 SHA256 无效')
    _, columns, _=TABLES[kind]
    row=[]
    for c in columns:
        v=str(d.get(c,''))
        if not v and c not in ('原图SHA256',): raise ValueError('缺少字段：'+c)
        row.append(v)
    return append(project,kind,row)

def status(project):
    peers=read_table(project/TABLES['peers'][0])
    latest={}
    for p in peers:
        key=tuple(p[:2])
        if key not in latest or datetime.fromisoformat(p[2])>datetime.fromisoformat(latest[key][2]):latest[key]=p
    good={p[0] for p in latest.values() if p[-1]=='合格'}
    metrics=read_table(project/TABLES['metrics'][0])
    missing=sum(r[6]=='缺失' for r in metrics)
    return f'合格同行账号：{len(good)}/20；缺口：{max(0,20-len(good))}\n指标记录：{len(metrics)}；缺失：{missing}\n'+('尚无后台基线，不能作增长归因。' if not metrics else '记录数不代表采集完整；复盘需核对同口径、同发布时长与证据。')

def check_package(project, files):
    rows=read_table(project/TABLES['assets'][0])
    by_hash={r[0]:r for r in rows}
    used=set()
    for r in rows:
        if r[5]=='已发布':used.update([r[0]]+r[4].split(','))
    for r in read_table(project/TABLES['published'][0]):
        used.update(r[3].split(','));used.update(r[4].split(','))
    for f in files:
        p=Path(f);p=p if p.is_absolute() else project/p
        h=sha(p);r=by_hash.get(h)
        if not r or r[2]!='发布候选' or r[5]!='通过':raise ValueError(f'未核实的发布候选：{p.name}')
        refs=r[4].split(',') if r[4] else []
        if not refs:raise ValueError('发布候选缺少原图追踪')
        for ref in refs:
            source=by_hash.get(ref)
            if not source or source[2]!='自家原图' or source[5]!='通过':raise ValueError('原图不是已核实的自家素材')
        if any(x in used for x in [h]+refs):raise ValueError('原图或成片已有成功发布记录')
    return '来源检查通过；仍需视觉真实性检查、平台核对及当前版本发布确认。'

def diagnose(project):
    rows=read_table(project/TABLES['metrics'][0])
    groups={}
    for r in rows:
        groups.setdefault((r[0],r[1],r[3],r[4],r[5],r[7]),[]).append(r)
    lines=['# 后台诊断草稿','',status(project),'', '| 作品/指标 | 两次读数 | 判断 | 下一步 |','|---|---|---|---|']
    for key,items in groups.items():
        items.sort(key=lambda r:datetime.fromisoformat(r[2]))
        last=items[-1];prev=items[-2] if len(items)>1 else None
        reason='只有一个时点，建立基线';action='同一统计口径补采，暂不归因'
        if last[6]=='缺失':reason='当前字段缺失';action='检查页面与统计区间，不补零'
        elif prev and prev[6]!='缺失':
            if last[5]=='累计' and last[7] in ('次','人','条'):
                delta=float(last[6])-float(prev[6])
                reason=f'累计变化 {delta:g}' if delta>=0 else '累计值下降，疑似修订，待核对'
                action='核对采集间隔；变化不代表封面或文案导致'
            else:reason='区间/时点/比例数据，仅并列比较';action='核对区间与定义，不当成日增量'
        values=(prev[6]+' → ' if prev else '')+last[6]
        lines.append('| '+' | '.join(map(encode,[last[1]+'/'+last[4],values,reason,action]))+' |')
    lines+=['','数据源与时间见后台数据.md。此为数值检查草稿，需人工/代理结合相同发布时长、形式、内容与流量来源完成结论。','下一轮拍摄任务写入项目 README；没有真实指标时只能给待验证假设。']
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=PROJECT)
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init');sub.add_parser('status');sub.add_parser('diagnose')
    a=sub.add_parser('ingest');a.add_argument('kind',choices=TABLES);a.add_argument('json_file',type=Path)
    a=sub.add_parser('check-package');a.add_argument('files',nargs='+')
    args=p.parse_args()
    try:
        if args.cmd=='init':
            print('按需记录：只有 ingest 真实数据时才建立文件，不生成空表。')
        elif args.cmd=='status':print(status(args.project))
        elif args.cmd=='diagnose':print(diagnose(args.project))
        elif args.cmd=='check-package':print(check_package(args.project,args.files))
        else: print(ingest(args.project,args.kind,json.loads(args.json_file.read_text())))
    except (ValueError,KeyError,OSError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
