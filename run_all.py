"""Run all five modules.  python run_all.py --scenario <deepmimo_name>   |   python run_all.py --synthetic"""
import argparse, json, os, time
import numpy as np
from rftwin import RadioConfig, load_deepmimo, load_synthetic
from rftwin import kpi, site_selection, outage, radiomap, beam, mobility, viz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", help="DeepMIMO scenario name (multi-BS for modules 1,2,5)")
    ap.add_argument("--synthetic", action="store_true", help="pipeline check on synthetic data (NOT results)")
    ap.add_argument("--mmwave", action="store_true", help="use the mmWave link budget preset")
    ap.add_argument("--target", type=float, default=0.95)
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--fast", action="store_true", help="smaller sweeps for a quick smoke run")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    P = lambda n: os.path.join(a.out, n)

    twin = load_synthetic() if a.synthetic or not a.scenario else load_deepmimo(a.scenario)
    cfg = RadioConfig.mmwave() if a.mmwave else RadioConfig.c_band()
    cfg.freq_hz = twin.freq_hz
    print(twin.summary())
    R = dict(twin=twin.summary(), source=twin.source)

    # --- KPIs / baseline maps
    rsrp = kpi.rsrp_matrix(twin.pathloss_db, cfg)
    k = kpi.serving_kpis(rsrp, cfg)
    R["baseline"] = kpi.summarize(twin, cfg, k)
    print("baseline:", R["baseline"])
    viz.plot_map(twin, k["rsrp"], "Best-server RSRP", P("map_rsrp.png"), "viridis", -120, -60, "dBm")
    viz.plot_map(twin, k["sinr_db"], "SINR", P("map_sinr.png"), "magma", -10, 30, "dB")
    viz.plot_map(twin, k["tput_mbps"], "Peak user throughput", P("map_tput.png"), "plasma", None, None, "Mbps")
    viz.plot_map(twin, ~kpi.coverage_mask(k, cfg) & twin.eligible, "Coverage holes (yellow)", P("map_holes.png"), "cividis")

    # --- 1 site selection
    if twin.n_bs >= 2:
        g = site_selection.greedy_sites(twin, cfg, a.target)
        ilp = site_selection.ilp_min_sites(twin, cfg, a.target)
        R["site_selection"] = dict(greedy=g, ilp=ilp)
        viz.plot_site_curve(twin, g, ilp, a.target, P("site_selection.png"))
        cov, kk = kpi.coverage_pct(twin, cfg, np.isin(np.arange(twin.n_bs), g["order"]))
        viz.plot_map(twin, kk["rsrp"], f"RSRP with greedy sites {g['order']}", P("map_greedy.png"),
                     "viridis", -120, -60, "dBm", sites=g["order"])
        print("site selection:", g, ilp)

        # --- 2 outage
        base, rows = outage.n_minus_1(twin, cfg)
        worst = rows[0]["idx"]
        h = outage.heal(twin, cfg, worst)
        R["outage"] = dict(n_minus_1=rows, healing=h)
        viz.plot_n1(base, rows, P("n_minus_1.png")); viz.plot_healing(h, P("healing.png"))
        act = np.ones(twin.n_bs, bool); act[worst] = False
        _, kh = kpi.coverage_pct(twin, cfg, act, np.array(h["offsets_db"]))
        viz.plot_map(twin, kh["rsrp"], f"After {h['failed']} failure + self-healing", P("map_healed.png"),
                     "viridis", -120, -60, "dBm", failed=worst)
        print("outage:", h)

    # --- 3 radio map reconstruction
    rows = radiomap.evaluate(twin, cfg, fracs=(0.02, 0.05) if a.fast else (0.01, 0.02, 0.05, 0.10),
                             trials=1 if a.fast else 2)
    R["radiomap"] = rows; viz.plot_radiomap_curves(rows, P("radiomap.png"))
    print("radiomap sample:", [r for r in rows if r["frac"] == 0.05 and r["mode"] == "route"])

    # --- 4 beam management
    if twin.paths is not None:
        b = beam.run(twin, cfg, ks=(1, 3, 5, 8))
        R["beam"] = b; viz.plot_beam(b, P("beam.png"))
        print("beam:", [x for x in b["results"] if x["pos_noise_m"] == 0])

    # --- 5 handover tuning
    if twin.n_bs >= 2:
        speeds = (60,) if a.fast else (30, 120)
        rows = []
        for sp in speeds:
            rows += mobility.sweep(twin, cfg, speed_kmh=sp, n_ue=100 if a.fast else 200,
                                   duration_s=60 if a.fast else 120,
                                   hysts=(0, 2, 4) if a.fast else (0, 1, 2, 3, 4, 6),
                                   ttts=(0.1, 0.4, 1.0) if a.fast else (0.1, 0.2, 0.4, 0.64, 1.0))
            viz.plot_ho_heatmap(rows, sp, P(f"handover_{sp}kmh.png"))
        R["handover"] = rows
        for sp in speeds:
            best = min((r for r in rows if r["speed_kmh"] == sp), key=lambda r: r["cost"])
            print(f"handover best @ {sp} km/h:", best)

    with open(P("results.json"), "w") as f:
        json.dump(R, f, indent=2, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print("saved ->", a.out)


if __name__ == "__main__":
    t = time.time(); main(); print(f"{time.time()-t:.0f}s")
