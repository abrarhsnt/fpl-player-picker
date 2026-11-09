"""Pick the best XI by trying every legal formation."""
import pandas as pd

FORMATIONS = [(3, 4, 3), (3, 5, 2), (4, 4, 2), (4, 3, 3),
              (4, 5, 1), (5, 3, 2), (5, 4, 1), (5, 2, 3)]


def best_xi(df, col="pred"):
    top = {p: df[df.pos == p].nlargest(5, col) for p in ["GKP", "DEF", "MID", "FWD"]}
    results, best = {}, None
    for d, m, f in FORMATIONS:
        xi = pd.concat([top["GKP"].head(1), top["DEF"].head(d),
                        top["MID"].head(m), top["FWD"].head(f)])
        if len(xi) < 11:
            continue
        total = float(xi[col].sum() + xi[col].max())  # captain counts double
        results[f"{d}-{m}-{f}"] = round(total, 2)
        if best is None or total > best[1]:
            best = (f"{d}-{m}-{f}", total, xi)
    return best[0], round(best[1], 2), best[2], results
