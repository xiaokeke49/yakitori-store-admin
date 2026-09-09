import importlib.util
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('records',Path(__file__).resolve().parents[1]/'scripts/records.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class RecordsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/"06_公域运营/产品展示冰箱";self.p.mkdir(parents=True)
 def tearDown(self):self.tmp.cleanup()
 def metric(self, value=None,time='2026-09-09T10:00:00+08:00'):
  return dict(zip(r.TABLES['metrics'][1],['test','note',time,'发布至采集','阅读','累计',value,'次','fixture（非真实数据）']))
 def test_missing_and_zero(self):
  r.ingest(self.p,'metrics',self.metric());r.ingest(self.p,'metrics',self.metric(0,'2026-09-10T10:00:00+08:00'))
  rows=r.read_table(self.p/'后台数据.md');self.assertEqual([x[6] for x in rows],['缺失','0'])
 def test_idempotent_and_conflict(self):
  r.ingest(self.p,'metrics',self.metric(1));self.assertIn('跳过',r.ingest(self.p,'metrics',self.metric(1)))
  with self.assertRaises(ValueError):r.ingest(self.p,'metrics',self.metric(2))
 def test_markdown_escape(self):
  d=self.metric(1);d['证据']='测试|a\nb & c';r.ingest(self.p,'metrics',d)
  self.assertEqual(r.read_table(self.p/'后台数据.md')[0][-1],d['证据'])
 def test_bad_number(self):
  for x in (-1,float('nan'),float('inf'),True):
   with self.assertRaises(ValueError):r.ingest(self.p,'metrics',self.metric(x))
 def test_peer_strict_threshold(self):
  base=dict(zip(r.TABLES['peers'][1],['a','url','2026-09-09T10:00:00+08:00',19,10,3,'是','是','fixture','control','']))
  r.ingest(self.p,'peers',base.copy());self.assertIn('0/20',r.status(self.p))
  base.update({'观察时间':'2026-09-10T10:00:00+08:00','平台评论':20});r.ingest(self.p,'peers',base.copy());self.assertIn('1/20',r.status(self.p))
  base.update({'观察时间':'2026-09-11T10:00:00+08:00','完整核实':'否'});r.ingest(self.p,'peers',base);self.assertIn('0/20',r.status(self.p))
 def test_interest_threshold(self):
  base=dict(zip(r.TABLES['peers'][1],['a','url','2026-09-09T10:00:00+08:00',20,10,2,'是','是','fixture','control','']))
  r.ingest(self.p,'peers',base.copy());self.assertIn('0/20',r.status(self.p))
  base.update({'观察时间':'2026-09-10T10:00:00+08:00','正向兴趣评论':3});r.ingest(self.p,'peers',base);self.assertIn('1/20',r.status(self.p))
 def test_demo_cannot_publish_even_renamed(self):
  f=self.p/'demo.png';f.write_bytes(b'demo fixture')
  r.ingest(self.p,'assets',{'文件':str(f),'用途':'策划示意','版本':'v1','验收':'通过','说明':'test'})
  renamed=self.p/'candidate.png';renamed.write_bytes(f.read_bytes())
  with self.assertRaises(ValueError):r.check_package(self.p,[str(renamed)])
 def test_publish_dedupe(self):
  src=self.p/'raw.jpg';src.write_bytes(b'raw fixture')
  out=self.p/'edited.jpg';out.write_bytes(b'edited fixture')
  r.ingest(self.p,'assets',{'文件':str(src),'用途':'自家原图','版本':'v1','验收':'通过','说明':'test'})
  r.ingest(self.p,'assets',{'文件':str(out),'用途':'发布候选','版本':'v1','验收':'通过','说明':'test','原图SHA256':r.sha(src)})
  self.assertIn('通过',r.check_package(self.p,[str(out)]))
  d=dict(zip(r.TABLES['published'][1],['2026-09-09T10:00:00+08:00','https://example.com/test','v1',r.sha(out),r.sha(src),'fixture']))
  r.ingest(self.p,'published',d)
  self.assertIn('跳过',r.ingest(self.p,'published',d))
  with self.assertRaises(ValueError):r.check_package(self.p,[str(out)])
 def test_negative_delta_not_zero(self):
  r.ingest(self.p,'metrics',self.metric(20));r.ingest(self.p,'metrics',self.metric(10,'2026-09-10T10:00:00+08:00'))
  self.assertIn('下降',r.diagnose(self.p))
if __name__=='__main__':unittest.main()
