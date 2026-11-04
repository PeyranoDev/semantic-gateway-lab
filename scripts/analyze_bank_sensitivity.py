"""Bank-sensitivity analysis: does the exact generator order depend on the valid-task bank?

Recomputes exact 120-call detection probabilities for valid-prefix extension and
valid-bank mutation on the recorded salon tables, under the full bank and under banks
with one task template removed. Random is bank-independent. Runs on existing tables.
"""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from integrations.salon.model import Action, VARIANT_TARGET
from integrations.salon_depth.model import (Table, detection_curve, extend_episode,
                                            mutation_episode, random_episode, run_program, summary)

VARIANTS = ("read_scope", "slot_capacity", "confirm_unpaid", "refund_replay")
BUDGET = 120

# The four task templates (parametrized per tenant), named by their role.
def template(kind, tenant, customer, staff):
    return {
        "confirm": [Action("reserve", customer, tenant), Action("pay", customer, tenant),
                    Action("confirm", staff, tenant)],
        "refund": [Action("reserve", customer, tenant), Action("pay", customer, tenant),
                   Action("cancel", customer, tenant), Action("refund", staff, tenant)],
        "rebook": [Action("reserve", customer, tenant), Action("cancel", customer, tenant),
                   Action("reserve", customer, tenant + "2")],
        "read": [Action("list_bookings", customer, tenant), Action("read_booking", customer, tenant)],
    }[kind]

TENANTS = (("a", "alice", "staff_a"), ("b", "bob", "staff_b"))
KINDS = ("confirm", "refund", "rebook", "read")

def bank(kinds):
    return [template(k, *t) for t in TENANTS for k in kinds]

def load(variant):
    raw = json.loads(gzip.decompress((ROOT / "results/history-depth/tables" / (variant + ".json.gz")).read_bytes()))
    return Table(raw)

def order(table, target, programs):
    random_p = summary(detection_curve(random_episode(table, target), BUDGET), BUDGET)[0]
    prefix = [run_program(table, p, target) for p in programs]
    extend_p = summary(detection_curve(extend_episode(table, target, programs), BUDGET, prefix), BUDGET)[0]
    mut_p = summary(detection_curve(mutation_episode(table, target, programs), BUDGET, prefix), BUDGET)[0]
    ps = {"random": random_p, "seed_extend": extend_p, "sequence_uniform": mut_p}
    return ps, sorted(ps, key=lambda m: -ps[m])

def main():
    banks = {"full": KINDS}
    for drop in KINDS:
        banks[f"drop_{drop}"] = tuple(k for k in KINDS if k != drop)
    result = {}
    for variant in VARIANTS:
        table, target = load(variant), VARIANT_TARGET[variant]
        full_order = None
        rows = {}
        for name, kinds in banks.items():
            ps, ordering = order(table, target, bank(kinds))
            rows[name] = {"p": {k: round(v, 4) for k, v in ps.items()}, "order": ordering}
            if name == "full":
                full_order = ordering
        rows["winner_stable"] = all(r["order"][0] == full_order[0] for r in rows.values()
                                    if isinstance(r, dict) and "order" in r)
        result[variant] = rows
    (ROOT / "results/history-depth/bank-sensitivity.json").write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n")
    for variant in VARIANTS:
        print(f"== {variant} (winner stable: {result[variant]['winner_stable']})")
        for name in ["full"] + [f"drop_{k}" for k in KINDS]:
            r = result[variant][name]
            print(f"  {name:12} {r['order'][0]:16} | " +
                  " ".join(f"{m}={r['p'][m]:.2f}" for m in ("random", "seed_extend", "sequence_uniform")))

if __name__ == "__main__":
    main()
