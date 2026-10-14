import ast
import gzip
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from fuzzlab.backend import Gateway
from fuzzlab.feedback import Corpus, project
from fuzzlab.fuzzer import Campaign
from fuzzlab.model import Action, fixture_approval
from fuzzlab.mutation import OPERATORS, SequenceMutator, legitimate_seeds
from fuzzlab.oracle import inspect
from fuzzlab.sequence import SequenceCampaign, replay_program, run_campaign

def deterministic(row):
    return {k:v for k,v in row.items() if k not in ("elapsed_s","gateway_p95_us")}

class SequenceTests(unittest.TestCase):
    def test_all_bootstrap_programs_are_legitimate(self):
        for program in legitimate_seeds():
            service=Gateway()
            for action in program:
                before=service.state.snapshot()
                response=service.execute(action)
                self.assertTrue(response["allowed"],action)
                self.assertEqual(inspect(before,action,response,service.state.snapshot()),[])

    def test_no_regression_or_oracle_import_in_generator(self):
        from fuzzlab import mutation
        tree=ast.parse(Path(mutation.__file__).read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        for name in ("scenarios","oracle","reserved","backend","sequence"):
            self.assertNotIn(name,imports)
        self.assertNotIn("regression_witnesses",Path(mutation.__file__).read_text())

    def test_seed_approvals_are_fresh_and_scoped(self):
        for program in legitimate_seeds():
            nonces=[]
            for action in program:
                if action.token:
                    claim=json.loads(action.token)["payload"]
                    self.assertEqual(claim["actor"],action.actor)
                    self.assertEqual(claim["document"],action.document)
                    nonces.append(claim["nonce"])
            self.assertEqual(len(nonces),len(set(nonces)))

    def test_mutations_keep_action_types_and_bounds(self):
        seeds=legitimate_seeds()
        engine=SequenceMutator(random.Random(7),depth=12)
        for source in seeds:
            for operator in OPERATORS:
                candidate,used=engine.mutate(source,seeds[-1],operator)
                self.assertTrue(candidate)
                self.assertLessEqual(len(candidate),12)
                self.assertEqual(used,operator)
                self.assertTrue(all(isinstance(a,Action) for a in candidate))
                self.assertEqual(replay_program(candidate)["violations"],[])

    def test_duplicate_preserves_exact_arguments_and_tokens(self):
        source=next(p for p in legitimate_seeds() if any(a.token for a in p))
        candidate,_=SequenceMutator(random.Random(11)).mutate(source,source,"duplicate")
        self.assertGreater(len(candidate),len(source))
        self.assertTrue(all(a in source for a in candidate))

    def test_mutation_rng_is_reproducible(self):
        left=SequenceMutator(random.Random(22))
        right=SequenceMutator(random.Random(22))
        sources=legitimate_seeds()
        for i in range(30):
            self.assertEqual(left.mutate(sources[i%len(sources)],sources[-1]),
                             right.mutate(sources[i%len(sources)],sources[-1]))

    def test_invalid_mutation_inputs(self):
        engine=SequenceMutator(random.Random(0))
        with self.assertRaises(ValueError):
            engine.mutate([],legitimate_seeds()[0])
        with self.assertRaises(ValueError):
            engine.mutate(legitimate_seeds()[0],[], "field")
        with self.assertRaises(ValueError):
            engine.mutate(legitimate_seeds()[0],legitimate_seeds()[0],"oracle")

    def test_recipient_ablation_drops_only_recipient_distinction(self):
        a,b=Gateway(),Gateway()
        a.execute(Action("initiate_share",target="bob"))
        b.execute(Action("initiate_share",target="mallory"))
        left,right=a.state.snapshot(),b.state.snapshot()
        self.assertNotEqual(project(left,"enriched"),project(right,"enriched"))
        self.assertEqual(project(left,"no_recipient"),project(right,"no_recipient"))

    def test_approval_ablation_drops_consumed_nonce_distinction(self):
        a,b=Gateway().state.snapshot(),Gateway().state.snapshot()
        b["used_nonces"]=["n1"]
        self.assertNotEqual(project(a,"enriched"),project(b,"enriched"))
        self.assertEqual(project(a,"no_approval"),project(b,"no_approval"))

    def test_owner_ablation_drops_ownership_relation(self):
        a,b=Gateway().state.snapshot(),Gateway().state.snapshot()
        b["documents"]["d1"]["owner"]="bob"
        self.assertNotEqual(project(a,"enriched"),project(b,"enriched"))
        self.assertEqual(project(a,"no_owner"),project(b,"no_owner"))

    def test_corpus_is_bounded_and_tracks_evictions(self):
        corpus=Corpus(2)
        program=legitimate_seeds()[0]
        for key in ("a","b","c"):
            corpus.remember(key,program)
        self.assertEqual(len(corpus.entries),2)
        self.assertNotIn("a",corpus.entries)
        self.assertEqual(corpus.evictions,1)

    def test_corpus_keeps_shorter_tested_program(self):
        corpus=Corpus()
        program=legitimate_seeds()[0]
        corpus.remember("key",program)
        corpus.remember("key",program[:2])
        corpus.remember("key",program)
        self.assertEqual(corpus.entries["key"],program[:2])

    def test_original_engine_output_is_unchanged(self):
        original=Campaign("enabled","wrong_recipient",seed=9,budget=250,depth=12).run()
        extended=run_campaign("enabled","wrong_recipient",9,250,12)
        for key,value in deterministic(original).items():
            self.assertEqual(value,extended[key],key)

    def test_fixed_controls_and_warmup_budget(self):
        for strategy in ("sequence_uniform","sequence_enabled","sequence_enriched",
                         "sequence_no_recipient","sequence_no_approval","sequence_enriched_uniform"):
            result=SequenceCampaign(strategy,budget=180,seed=4).run()
            self.assertFalse(result["detected"],strategy)
            self.assertEqual(result["calls"],180)
            self.assertEqual(result["calls"],result["allowed"]+result["denied"])
            self.assertGreater(result["bootstrap_calls"],0)
            self.assertLessEqual(result["bootstrap_calls"]+result["source_prefix_calls"],180)

    def test_tiny_budget_includes_seed_execution(self):
        for budget in (1,2,4,9):
            result=SequenceCampaign(budget=budget).run()
            self.assertEqual(result["calls"],budget)
            self.assertEqual(result["bootstrap_calls"],budget)
            self.assertTrue(result["right_censored"])

    def test_sequence_campaign_determinism(self):
        for strategy in ("sequence_enabled","sequence_enriched"):
            self.assertEqual(deterministic(SequenceCampaign(strategy,"wrong_recipient",5,350).run()),
                             deterministic(SequenceCampaign(strategy,"wrong_recipient",5,350).run()))

    def test_hash_seed_does_not_change_sequence_results(self):
        code=('import json; from fuzzlab.sequence import SequenceCampaign; '
              'r=SequenceCampaign("sequence_enriched","approval_replay",seed=2,budget=150).run(); '
              'r.pop("elapsed_s");r.pop("gateway_p95_us");print(json.dumps(r,sort_keys=True))')
        outputs=[subprocess.check_output([sys.executable,"-c",code],text=True,
                 env={**os.environ,"PYTHONHASHSEED":value}) for value in ("1","999")]
        self.assertEqual(*outputs)

    def test_reserved_variants_have_independent_oracle_witnesses(self):
        cases={"list_scope":[Action("list_documents")],
               "unauthorized_update":[Action("update_document",actor="bob",content="changed")],
               "cross_department_share":[Action("initiate_share",target="carol")]}
        for variant,trace in cases.items():
            self.assertTrue(replay_program(trace,variant)["violations"],variant)
            self.assertEqual(replay_program(trace)["violations"],[])

    def test_approval_replay_is_detectable_without_bug_graph(self):
        trace=[Action("request_delete"),Action("delete_document",token=fixture_approval()),
               Action("create_document"),Action("request_delete"),
               Action("delete_document",token=fixture_approval())]
        self.assertIn("APPROVAL_REPLAY",replay_program(trace,"approval_replay")["violations"])
        self.assertEqual(replay_program(trace)["violations"],[])

    def test_invalid_campaign_settings(self):
        for kwargs in ({"budget":0},{"budget":True},{"depth":1},{"capacity":0},
                       {"strategy":"unknown"},{"mutant":"unknown"}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                SequenceCampaign(**kwargs)

    def test_compact_cli_output_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            config=root/"config.json"
            config.write_text(json.dumps(dict(seeds=[0],strategies=["sequence_enabled","sequence_enriched"],
                mutants=["fixed","list_scope"],budget=50,depth=12,capacity=32)))
            command=[sys.executable,"-m","fuzzlab.sequence","run","--config",str(config),"--out",str(root/"out")]
            subprocess.run(command,check=True,capture_output=True)
            rows=[json.loads(line) for line in gzip.decompress((root/"out/raw.jsonl.gz").read_bytes()).decode().splitlines()]
            self.assertEqual(len(rows),4)
            self.assertEqual(sum(r["detected"] for r in rows),2)
            self.assertTrue((root/"out/paired.json").exists())
            self.assertTrue((root/"out/validation.json").exists())
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
