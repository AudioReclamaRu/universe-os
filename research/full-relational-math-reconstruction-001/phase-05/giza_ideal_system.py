"""GIZA PRIME Phase 05 — ideal system reproducer.

All source integer measurements are stored as paired binary/ternary strings.
All reported numerical outputs use paired numerals or paired fractions.
No legacy UNIVERSE code is imported.
"""
from __future__ import annotations
from itertools import combinations
from math import acos, atan, cos, degrees, hypot, radians, sqrt, tan
from fractions import Fraction

def decode(b: str, t: str) -> int:
    x, y = int(b, 2), int(t, 3)
    if x != y:
        raise ValueError(f"Bad paired numeral: {b}₂ / {t}₃")
    return x

def enc(n: int, base: int) -> str:
    if n < 0:
        return "-" + enc(-n, base)
    if n == 0:
        return "0"
    digits = "012"
    out = ""
    while n:
        n, r = divmod(n, base)
        out = digits[r] + out
    return out

def pair(n: int) -> str:
    return f"<{enc(n, 2)}₂ | {enc(n, 3)}₃>"

def fraction(n: int, d: int = 1) -> str:
    f = Fraction(n, d)
    return f"{pair(f.numerator)} / {pair(f.denominator)}"

def fmt(x: float, unit: str = "", scale: int = 1000) -> str:
    text = fraction(round(x * scale), scale)
    return text + (f" {unit}" if unit else "")

# GPMP base centres in local grid, northing/easting in decimetres.
GPMP = {
    "Khufu": (decode("11110100001001000000","1212210202001"),
              decode("10011000100101101000000","100102000201012")),
    "Khafre": (decode("11110011010001101000","1212121212210"),
               decode("10011000011111000110100","100101212010111")),
    "Menkaure": (decode("11110010010101010111","1212102120221"),
                 decode("10011000011010011011001","100101201211210")),
}

# Nominal original pyramid dimensions, millimetres.
PYRAMIDS = {
    "Khufu": ((decode("111000001110111001","102200221201"),)*2,
              decode("100011110010011110","21110002021")),
    "Khafre": ((decode("110100100011010010","101221021020"),)*2,
               decode("100011000010001100","21021211211")),
    "Menkaure": ((decode("11000111100111000","12012012012"),
                  decode("11001100010011000","12022111002")),
                 decode("1111110111101000","10022011102")),
}

# Khentkaus exposed bedrock base, GLSS dimensions, millimetres.
K = {
    "a": decode("1011000110111100","2022102012"),
    "b": decode("1011010110100100","2100210020"),
    "rock_h": decode("10011100010000","111201101"),
    "super_h": decode("1110101001100","101021210"),
    "rock_h_AERAGRAM": decode("10101011111000","120002102"),
    "super_h_AERAGRAM": decode("1101101011000","100121021"),
}

# Map-point proxies at 10^-5 degree; they are not survey-tied parent-mass centres.
MAP_E5 = {
    "Khufu": (decode("1011011011111010011101","12122022100222"),
              decode("1011111000000111001101","12212011210220")),
    "Great_Sphinx": (decode("1011011011110100011000","12122021211120"),
                     decode("1011111000001100100000","12212012021110")),
    "Khentkaus": (decode("1011011011110001100011","12122021120212"),
                  decode("1011111000001001001101","12212011222122")),
}

QUARRY = {
    "north_width": decode("111000001001110000","102200111112"),
    "length": decode("1100001101010000000","202022200211"),
    "depth": decode("111010100110000","1112011010"),
    "circle_radius": decode("110000110101000000","101011100102"),
}

DELTAS = [
    decode("110010","1212"), decode("111101","2021"),
    decode("10101","210"), decode("100100","1100"),
    decode("100101","1101"),
]

def gpmp_local():
    n0, e0 = GPMP["Khufu"]
    return {k: ((e-e0)/10, (n-n0)/10) for k,(n,e) in GPMP.items()}

def angle_at(a, v, c):
    u=(a[0]-v[0],a[1]-v[1]); w=(c[0]-v[0],c[1]-v[1])
    z=(u[0]*w[0]+u[1]*w[1])/(hypot(*u)*hypot(*w))
    return degrees(acos(max(-1,min(1,z))))

def main():
    print("GIZA PRIME — PHASE 05 IDEAL SYSTEM AUDIT")
    print("RAW OBSERVATIONS and IDEAL PARAMETERS are kept separate.")

    gp=gpmp_local()
    names=("Khufu","Khafre","Menkaure")
    print("\nPYRAMID CENTRE TRIANGLE")
    for a,b in combinations(names,2):
        d=hypot(gp[a][0]-gp[b][0],gp[a][1]-gp[b][1])
        print(f"{a}--{b}: {fmt(d,'m')}")
    for v,a,c in (("Khufu","Khafre","Menkaure"),
                  ("Khafre","Khufu","Menkaure"),
                  ("Menkaure","Khufu","Khafre")):
        print(f"angle at {v}: {fmt(angle_at(gp[a],gp[v],gp[c]),'°',1_000_000)}")
    vx,vy=gp["Menkaure"]
    axis_len=hypot(vx,vy); ux,uy=vx/axis_len,vy/axis_len
    px,py=-uy,ux; kx,ky=gp["Khafre"]
    print(f"Khafre along-axis projection: {fmt(kx*ux+ky*uy,'m')}")
    print(f"Khafre cross-axis offset: {fmt(kx*px+ky*py,'m')}")
    print(f"centre-triangle area: {fmt(abs(vx*ky-vy*kx)/2,'m²',10)}")

    phi=(1+sqrt(5))/2
    print("\nPYRAMID SECTION PROPORTIONS")
    for name,(spans,hmm) in PYRAMIDS.items():
        h=hmm/1000
        for j,bmm in enumerate(spans):
            if spans[0]==spans[1] and j==1: continue
            b=bmm/1000; a=b/2
            eta=sqrt(1+(h/a)**2)
            print(f"{name} axis {pair(j+1)}: H/B={fmt(h/b,'',1_000_000)}; "
                  f"slant-apothem/half-base={fmt(eta,'',1_000_000)}; "
                  f"deviation from phi={fmt(eta-phi,'',1_000_000)}")

    mean=sum(DELTAS)/len(DELTAS)
    median=sorted(DELTAS)[len(DELTAS)//2]
    lo,hi=min(DELTAS),max(DELTAS)
    print("\nEIGHT HALF-FACE IDEAL FAMILY")
    print("each pyramid: N_L,N_R,E_L,E_R,S_L,S_R,W_L,W_R")
    print(f"Menkaure observed half-wall Δ: {[pair(x) for x in DELTAS]} arcmin")
    print(f"H1 mean Δ={pair(round(mean))}; H2 range={pair(lo)}..{pair(hi)} arcmin")
    for name,(spans,hmm) in PYRAMIDS.items():
        bset=spans if spans[0]!=spans[1] else (spans[0],)*4
        sides=(("N",bset[0]),("S",bset[0]),("E",bset[1]),("W",bset[1])) if len(bset)==2 else tuple(zip(("N","E","S","W"),bset))
        for side,bmm in sides:
            b=bmm/1000
            for model,delta in (("H0",0),("H1",mean),("H2-low",lo),("H2-high",hi)):
                sagitta=(b/2)*tan(radians(delta/60)/2)
                print(f"{name} {side} {model}: half-face turns ±{fmt(delta/2,'arcmin')}; "
                      f"ideal central sagitta={fmt(sagitta,'m')}")

    a,b=K["a"]/1000,K["b"]/1000
    print("\nKHENTKAUS BEDROCK MASS")
    print(f"exposed base spans: {fmt(a,'m')} × {fmt(b,'m')}")
    print(f"GLSS bedrock / superstructure heights: {fmt(K['rock_h']/1000,'m')} / {fmt(K['super_h']/1000,'m')}")
    print(f"AERAGRAM source bedrock / superstructure heights: {fmt(K['rock_h_AERAGRAM']/1000,'m')} / {fmt(K['super_h_AERAGRAM']/1000,'m')}")
    print("K0=exposed bedrock core; K1=pre-quarry parent mass; K2=stratigraphically registered parent mass.")

    r=QUARRY["circle_radius"]/1000
    qw=QUARRY["north_width"]/1000
    ql=QUARRY["length"]/1000
    qd=QUARRY["depth"]/1000
    b=PYRAMIDS["Khufu"][0][0]/1000
    h=PYRAMIDS["Khufu"][1]/1000
    gross=qw*ql*qd
    pyramid=b*b*h/3
    print("\nKHENTKAUS-CENTRED QUARRY IDEAL")
    print(f"ideal circle radius / diameter: {fmt(r,'m')} / {fmt(2*r,'m')}")
    print("ideal circumference=2πR; ideal area=πR²")
    print(f"north quarry width / Khufu base side: {fmt(qw,'m')} / {fmt(b,'m')}")
    print(f"width/base ratio: {fmt(qw/b,'',1_000_000)}")
    print(f"rough quarry bounding volume: {fmt(gross,'m³',10)}")
    print(f"Khufu B²H/3 volume: {fmt(pyramid,'m³',10)}")
    print(f"bounding-volume / pyramid-volume ratio: {fmt(gross/pyramid,'',1_000_000)}")
    print("material ledger: gross extraction = usable blocks + channels + waste + retained rock.")

    kh_lat=MAP_E5["Khufu"][0]/100000
    kh_lon=MAP_E5["Khufu"][1]/100000
    lat0=radians(kh_lat)
    north_per_degree=111132.92
    east_per_degree=111412.84*cos(lat0)-93.5*cos(3*lat0)
    points={k:v for k,v in gp.items()}
    for name,(lat_i,lon_i) in MAP_E5.items():
        if name=="Khufu": continue
        points[name]=((lon_i/100000-kh_lon)*east_per_degree,
                      (lat_i/100000-kh_lat)*north_per_degree)
    order=("Khufu","Khafre","Menkaure","Great_Sphinx","Khentkaus")
    print("\nFIVE-NODE MAP-PROXY DISTANCES")
    for x,y in combinations(order,2):
        print(f"{x}--{y}: {fmt(hypot(points[x][0]-points[y][0],points[x][1]-points[y][1]),'m')}")
    da=hypot(points["Khufu"][0]-points["Great_Sphinx"][0],points["Khufu"][1]-points["Great_Sphinx"][1])
    db=hypot(points["Khafre"][0]-points["Khentkaus"][0],points["Khafre"][1]-points["Khentkaus"][1])
    print("IDEAL DESIGN INVARIANT: d(P_Khufu,M_Sphinx)=d(P_Khafre,M_Khentkaus)=L*")
    print(f"map-proxy dA / dB: {fmt(da,'m')} / {fmt(db,'m')}")
    print(f"symmetric initial seed sqrt(dA*dB): {fmt(sqrt(da*db),'m')}")
    print(f"map-proxy residual / relative mismatch: {fmt(abs(da-db),'m')} / {fmt(abs(da-db)/((da+db)/2),'',1_000_000)}")
    print("Map pins are not parent-mass datums or common-control survey points.")

    d1=decode("110000101","112102")/10
    h1=decode("11011111","22021")/1000
    d2=decode("11111011","100022")
    h2=decode("1100011","10200")/1000
    print("\nSPHINX–KHENTKAUS STRATIGRAPHIC TIE")
    print(f"G32--G23: distance={fmt(d1,'m')}; height difference={fmt(h1,'m')}; slope={fmt(degrees(atan(h1/d1)),'°',1_000_000)}")
    print(f"G32--G24: distance={fmt(d2,'m')}; height difference={fmt(h2,'m')}; slope={fmt(degrees(atan(h2/d2)),'°',1_000_000)}")
    print("The field survey correlates marly/nummulitic beds near Khentkaus with the Sphinx neck/head sequence.")
    print("\nEND: system geometry reproduced; broader physical functions remain further research layers.")

if __name__=="__main__":
    main()
