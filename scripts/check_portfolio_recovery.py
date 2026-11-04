"""Compare every saved pre-interruption campaign with the full unchanged rerun."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def compare(partial='results/salon-v08-interrupted', complete='results/salon-v08'):
    partial, complete = Path(partial), Path(complete)
    info=json.loads((partial/'interruption.json').read_text())
    started=json.loads((partial/'started.json').read_text())
    manifest=json.loads((complete/'manifest.json').read_text())
    assert started['config'] == manifest['config']
    assert started['source_sha256'] == manifest['source_sha256']
    old_bytes=gzip.decompress((partial/'partial.jsonl.gz').read_bytes())
    new_bytes=gzip.decompress((complete/'raw.jsonl.gz').read_bytes())
    assert hashlib.sha256(old_bytes).hexdigest() == info['raw_sha256']
    assert hashlib.sha256(new_bytes).hexdigest() == manifest['raw_sha256']
    old=[json.loads(s) for s in old_bytes.splitlines()]
    new=[json.loads(s) for s in new_bytes.splitlines()]
    assert len(old) == info['completed_campaigns'] == 810
    assert len(new) == manifest['runs'] == 900
    for i,(a,b) in enumerate(zip(old,new)):
        # No outcome, cost, trace, seed or scheduling field is excluded.
        a.pop('elapsed_s'); b.pop('elapsed_s')
        assert a == b,(i,a['variant'],a['mode'],a['seed'],a['budget'])
    result={'compared_campaign_pairs':len(old),'identical_except_elapsed_s':True,
            'unchanged_config_and_measured_source':True,
            'counted_in_primary_analysis':len(new),
            'excluded_duplicate_partial_campaigns':len(old)}
    print(json.dumps(result,sort_keys=True))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial',default='results/salon-v08-interrupted')
    parser.add_argument('--complete',default='results/salon-v08')
    args=parser.parse_args();compare(args.partial,args.complete)
