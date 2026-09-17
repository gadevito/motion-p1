import re
t = open("models/gomo_classify.py").read()
t = t.replace('ap.add_argument("--emb"',
 'ap.add_argument("--dump-metrics", type=str, default="", help="CSV con precision/recall/F1 per classe, confusione e calibrazione")\nap.add_argument("--emb"')
old = '''def scores(P, Y):
    P = P.reshape(-1, 3); Y = Y.reshape(-1); v = Y >= 0; P, Y = P[v], Y[v]
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1)
    wce = float(np.sum(Wnp[Y] * -np.log(pt)) / np.sum(Wnp[Y]))    # normalize by sum of weights
    pred = P.argmax(1); f1 = []
    for k in range(3):
        tp = np.sum((pred == k) & (Y == k)); fp = np.sum((pred == k) & (Y != k)); fn = np.sum((pred != k) & (Y == k))
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
    return wce, float(np.mean(f1)), float(np.sum((pred == 2) & (Y == 2)) / max(np.sum(Y == 2), 1))'''
new = '''DUMP = []
def scores(P, Y, tag=""):
    P = P.reshape(-1, 3); Y = Y.reshape(-1); v = Y >= 0; P, Y = P[v], Y[v]
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1)
    wce = float(np.sum(Wnp[Y] * -np.log(pt)) / np.sum(Wnp[Y]))    # normalize by sum of weights
    pred = P.argmax(1); f1 = []
    for k in range(3):
        tp = np.sum((pred == k) & (Y == k)); fp = np.sum((pred == k) & (Y != k)); fn = np.sum((pred != k) & (Y == k))
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
        if args.dump_metrics and tag:
            DUMP.append((tag, "class", k, float(pr), float(rc), float(f1[-1]), int((Y == k).sum())))
    if args.dump_metrics and tag:
        for i in range(3):
            for j in range(3):
                DUMP.append((tag, "conf", i*3+j, float(((Y == i) & (pred == j)).sum()), i, j, 0))
        pr_red = P[:, 2]; bins = np.clip((pr_red * 10).astype(int), 0, 9); ece = 0.0
        for b in range(10):
            m = bins == b
            if m.sum():
                pm, fo = float(pr_red[m].mean()), float((Y[m] == 2).mean())
                ece += m.sum()/len(Y) * abs(pm - fo)
                DUMP.append((tag, "calib", b, pm, fo, 0.0, int(m.sum())))
        DUMP.append((tag, "ece", 0, float(ece), 0.0, 0.0, len(Y)))
    return wce, float(np.mean(f1)), float(np.sum((pred == 2) & (Y == 2)) / max(np.sum(Y == 2), 1))'''
assert old in t; t = t.replace(old, new, 1)
t = re.sub(r'rows\.append\(\((.+?), HL\[h\], \*scores\((\w+), (\w+)\)\)\)',
           r'rows.append((\1, HL[h], *scores(\2, \3, tag=str(\1) + "|" + str(HL[h]))))', t)
t = t.replace('    new.to_csv(args.out, index=False); return new',
'''    new.to_csv(args.out, index=False)
    if args.dump_metrics and DUMP:
        pd.DataFrame(DUMP, columns=["tag","kind","idx","a","b","c","n"]).to_csv(args.dump_metrics, index=False)
        print(f"[metrics] -> {args.dump_metrics}")
    return new''')
open("models/gomo_classify.py","w").write(t); print("patch metriche applicata")
