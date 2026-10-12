import unittest, tempfile, struct, math
from pathlib import Path
from price_research import decode,metrics,buy_hold,dividend_scenario,signal_action
def row(d,o=10,c=10):return dict(date=d,open=o,close=c)
class PriceTests(unittest.TestCase):
    def test_fixed_returns_drawdown(self):
        m=metrics([100,120,90,110]);self.assertAlmostEqual(m['price_return'],.1);self.assertAlmostEqual(m['max_drawdown'],-.25)
    def test_flat(self):self.assertEqual(metrics([1,1,1])['max_drawdown'],0)
    def test_fee_and_cash_reference(self):
        a,m=buy_hold([row('2024-04-25'),row('2024-04-26',c=11)],1000,100,0,10)
        self.assertEqual(a[0]['units'],90);self.assertEqual(a[0]['cash'],91);self.assertEqual(m['fees'],9);self.assertEqual(a[-1]['equity'],1081)
    def test_no_overdraft(self):
        a,m=buy_hold([row('2024-04-25',o=100)],10);self.assertEqual(m['trades'],0);self.assertEqual(a[0]['cash'],10)
    def test_fee_sensitivity(self):
        rows=[row('2024-04-25'),row('2024-04-26',c=11)]
        self.assertGreater(buy_hold(rows,fee_bps=0)[1]['end_equity'],buy_hold(rows,fee_bps=10)[1]['end_equity'])
    def test_signal_boundaries(self):
        for x,a in [(.99,'SELL'),(1,'HOLD'),(1.5,'HOLD'),(1.5001,'NORMAL'),(3,'NORMAL'),(3.001,'DOUBLE')]:self.assertEqual(signal_action(x),a)
    def test_missing_signal_blocked(self):
        for x in [None,float('nan')]:
            with self.assertRaises(ValueError):signal_action(x)
    def test_dividend_waits_payment_and_weekend(self):
        rows=[row('2024-04-25'),row('2024-04-26',c=9),row('2024-04-29',o=9,c=9)]
        e=[dict(record_date='2024-04-25',ex_date='2024-04-26',declared_payment_date='2024-04-26',cash_per_share=1)]
        a,f,m=dividend_scenario(rows,e,1000,0,0,1)
        self.assertEqual(a[1]['receivable'],100);self.assertEqual(a[1]['dividend_cash'],0);self.assertEqual(a[1]['units'],100)
        self.assertEqual(a[2]['dividend_cash'],100);self.assertEqual(a[2]['units'],111);self.assertEqual(a[2]['receivable'],0);self.assertEqual(a[2]['equity'],1000)
    def test_record_date_unavailable_skipped(self):
        rows=[row('2024-04-25'),row('2024-04-26')];e=[dict(record_date='2024-04-24',ex_date='2024-04-25',declared_payment_date='2024-04-25',cash_per_share=1)]
        a,f,m=dividend_scenario(rows,e,1000,0,0,1);self.assertEqual(m['credited_events'],0);self.assertEqual(len(m['skipped_record_dates']),1)
    def test_duplicate_dividends_rejected(self):
        e=dict(record_date='2024-04-25',ex_date='2024-04-26',declared_payment_date='2024-04-26',cash_per_share=1)
        with self.assertRaises(ValueError):dividend_scenario([row('2024-04-25')],[e,e])
    def test_truncated_raw_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';p.write_bytes(b'bad')
            with self.assertRaises(ValueError):decode(p,'510300')
    def test_decoder_units_and_uniqueness(self):
        b=struct.pack('<IIIIIfII',20240425,1000,1100,900,1050,100.,100,0)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';p.write_bytes(b);self.assertEqual(decode(p,'159307')[0]['close'],1.05)
            p.write_bytes(b+b)
            with self.assertRaises(ValueError):decode(p,'159307')
    def test_bad_ohlc_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';p.write_bytes(struct.pack('<IIIIIfII',20240425,1000,900,800,1050,100.,100,0))
            with self.assertRaises(ValueError):decode(p,'159307')
    def test_future_date_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';p.write_bytes(struct.pack('<IIIIIfII',20990101,1000,1100,900,1050,100.,100,0))
            with self.assertRaises(ValueError):decode(p,'159307')
if __name__=='__main__':unittest.main()
