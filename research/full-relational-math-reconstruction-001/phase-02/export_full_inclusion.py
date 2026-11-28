#!/usr/bin/env python3
"""Export all strict nonempty face inclusions of Q7 (standard library only)."""
import argparse,csv,itertools
from pathlib import Path

SYMBOLS="-0+"
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("data"))
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    states=["".join(x) for x in itertools.product(SYMBOLS,repeat=7)]
    ids={s:i for i,s in enumerate(states)}
    rows=[]
    for upper in states:
        free=[i for i,c in enumerate(upper) if c=="0"]
        for replacements in itertools.product(SYMBOLS,repeat=len(free)):
            lower=list(upper)
            for i,c in zip(free,replacements):
                lower[i]=c
            lower="".join(lower)
            if lower!=upper:
                rows.append((ids[lower],ids[upper],lower,upper,len(free)))
    assert len(rows)==75938, len(rows)
    path=args.out/"Q7_FACE_INCLUSION.csv"
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(("lower_face_id","upper_face_id","lower_state","upper_state","upper_dimension"))
        w.writerows(rows)
    print(f"PASS: exported {len(rows)} strict nonempty inclusion pairs to {path}")
if __name__=="__main__":
    main()
