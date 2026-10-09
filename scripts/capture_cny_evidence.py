"""Append-only official-document captures for the second evidence round.

An HTTP success is a byte receipt, not confirmation of tax applicability.
Reruns retain old receipts and write a new timestamped attempt directory.
"""
from pathlib import Path
import argparse, concurrent.futures, datetime, hashlib, json, urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/v32-cny/evidence-round2'
SOURCES = [
 ('510300-listing-original', '510300上市公告原版法定披露', 'https://epaper.stcn.com/paper/zqsb/page/1/2012-05/23/D006/20120523D006_pdf.pdf', '2012-05-23'),
 ('510300-annual2012', '510300 2012年年度报告', 'https://www.sse.com.cn/disclosure/fund/announcement/c/2013-03-27/510300_2012_n.pdf', '2013-03-28'),
 ('510300-feechange2024', '510300降费及合同修订公告', 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2024-11-20/510300_20241120_FOBE.pdf', '2024-11-20'),
 ('513500-prospectus2022', '513500 2022更新招募说明书', 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2022-11-09/513500_20221109_77JP.pdf', '2022-11-09'),
 ('513500-summary2024', '513500 2024产品资料概要', 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2024-06-26/513500_20240626_XXG0.pdf', '2024-06-26'),
 ('fund-tax1998-scope', '财税字〔1998〕55号·封闭式证券基金范围', 'https://fgk.chinatax.gov.cn/zcfgk/c102416/c5202736/content.html', '1998-08-06'),
 ('H11006-factsheet-followup', 'H11006事实表补证尝试', 'https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/H11006factsheet.pdf', None),
]

def capture(spec, directory):
 sid, name, url, published = spec
 now = datetime.datetime.now(datetime.timezone.utc).isoformat()
 row = dict(id=sid, name=name, url=url, published_at=published,
            downloaded_at=now, observed_at=now, evidence_level='A',
            publication_timestamp_verified=False, manual_processing=False,
            proxy=False, publicly_reviewable=True, frequency='official disclosure',
            coverage=None, original_sha256=None, status='FAILED')
 try:
  req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req, timeout=25) as response:
   content = response.read(15_000_001)
   if len(content)>15_000_000: raise ValueError('capture size limit')
   row.update(http_status=response.status, content_type=response.headers.get('Content-Type'))
  h = hashlib.sha256(content).hexdigest()
  p = directory / f'{sid}-{h}.raw'
  if p.exists(): assert p.read_bytes()==content
  else: p.write_bytes(content)
  row.update(original_sha256=h, file=str(p.relative_to(ROOT)), bytes=len(content),
             status='BYTES SAVED / CONTENT AND APPLICATION REQUIRE REVIEW')
 except Exception as error:
  row['error'] = type(error).__name__ + ': ' + str(error)[:200]
 return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--ids',nargs='*');args=parser.parse_args()
 assert (DEST/'protocol.json').exists(), 'register scope before capture'
 stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 directory = DEST / 'attempts' / stamp
 directory.mkdir(parents=True, exist_ok=False)
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  selected=[x for x in SOURCES if not args.ids or x[0] in args.ids]
  assert selected, 'no registered source selected'
  rows = list(pool.map(lambda spec:capture(spec,directory), selected))
 (directory/'receipts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'directory':str(directory), 'captured':sum(bool(x['original_sha256']) for x in rows),
                   'failed':sum(x['status']=='FAILED' for x in rows)},ensure_ascii=False))

if __name__=='__main__':main()
