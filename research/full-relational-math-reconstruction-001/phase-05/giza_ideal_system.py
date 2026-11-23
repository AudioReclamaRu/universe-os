"""GIZA PRIME Phase 05 — ideal system reproducer.

All source integer measurements are stored as paired binary/ternary strings.
All reported numerical outputs use paired numerals or paired fractions.
No legacy UNIVERSE code is imported.
"""
from __future__ import annotations
from itertools import combinations
from math import acos, atan, atan2, cos, degrees, hypot, radians, sqrt, tan
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


# GLSS Table 10 — ten B01..B10 markers on the top of the lower natural
# Khentkaus bedrock base. Northing/easting are GPMP metres stored as cm;
# height is GPMP metres stored as mm. All three integers are paired.
KHENTKAUS_B_MARKERS = [
    (decode("100101111010000110011010","200200212102101"),
     decode("10111110110010001101001001","10111002220221101"),
     decode("1001110011100000","2001002102")),
    (decode("100101111010001000100000","200200212121100"),
     decode("10111110110010011001010001","10111002222000010"),
     decode("1001101011110110","2000102021")),
    (decode("100101111001101101001111","200200210012201"),
     decode("10111110110010011001101001","10111002222001000"),
     decode("1001110001111100","2000221201")),
    (decode("100101111001010110110000","200200201020102"),
     decode("10111110110010010001001111","10111002221022002"),
     decode("1001110001101000","2000220222")),
    (decode("100101111001010001101000","200200200210021"),
     decode("10111110110010000010010100","10111002212222201"),
     decode("1001100101011100","1222212002")),
    (decode("100101111001010000110011","200200200201022"),
     decode("10111110110001111000100010","10111002212010112"),
     decode("1001101001111110","2000020211")),
    (decode("100101111001010010110110","200200200220011"),
     decode("10111110110001101001111111","10111002210212001"),
     decode("1001110000101100","2000211202")),
    (decode("100101111001101010000101","200200202221020"),
     decode("10111110110001101010011000","10111002210212222"),
     decode("1001110001011110","2000220121")),
    (decode("100101111010000001111111","200200212000220"),
     decode("10111110110001110000000111","10111002211101120"),
     decode("1001110100110000","2001012101")),
    (decode("100101111010000011101010","200200212011212"),
     decode("10111110110001111100100111","10111002212111012"),
     decode("1001110001111100","2000221201")),
]

def gpmp_local():
    n0, e0 = GPMP["Khufu"]
    return {k: ((e-e0)/10, (n-n0)/10) for k,(n,e) in GPMP.items()}

def angle_at(a, v, c):
    u=(a[0]-v[0],a[1]-v[1]); w=(c[0]-v[0],c[1]-v[1])
    z=(u[0]*w[0]+u[1]*w[1])/(hypot(*u)*hypot(*w))
    return degrees(acos(max(-1,min(1,z))))


def khentkaus_glss_b_geometry():
    """Reconstruct a provisional plan envelope and top-surface datum from GLSS B markers."""
    markers = [
        (north_cm/100, east_cm/100, z_mm/1000)
        for north_cm, east_cm, z_mm in KHENTKAUS_B_MARKERS
    ]
    mean_n = sum(p[0] for p in markers) / len(markers)
    mean_e = sum(p[1] for p in markers) / len(markers)
    mean_z = sum(p[2] for p in markers) / len(markers)

    # Convex hull of the measured plan points (x=E, y=N).
    pts = sorted(set((p[1], p[0]) for p in markers))
    def turn(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower = []
    for q in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    upper = []
    for q in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull = lower[:-1] + upper[:-1]
    hull_area = abs(sum(
        hull[i][0]*hull[(i+1) % len(hull)][1] -
        hull[(i+1) % len(hull)][0]*hull[i][1]
        for i in range(len(hull))
    ) / 2)
    hull_perimeter = sum(
        hypot(hull[i][0]-hull[(i+1) % len(hull)][0],
              hull[i][1]-hull[(i+1) % len(hull)][1])
        for i in range(len(hull))
    )

    # Principal horizontal axis of the measured B-marker cloud.
    nvals = [p[0] for p in markers]
    evals = [p[1] for p in markers]
    var_n = sum((n-mean_n)**2 for n in nvals)/len(markers)
    var_e = sum((e-mean_e)**2 for e in evals)/len(markers)
    cov_ne = sum((n-mean_n)*(e-mean_e) for n,e in zip(nvals,evals))/len(markers)
    principal_bearing = (degrees(0.5*atan2(2*cov_ne, var_n-var_e)) + 180) % 180

    # Least-squares plane z = a + gE*(E-Ebar) + gN*(N-Nbar).
    # Solve the 2x2 centred normal equations explicitly.
    sEE = sum((e-mean_e)**2 for e in evals)
    sNN = sum((n-mean_n)**2 for n in nvals)
    sEN = sum((e-mean_e)*(n-mean_n) for n,e in zip(nvals,evals))
    sEZ = sum((e-mean_e)*(z-mean_z) for e,(_,_,z) in zip(evals,markers))
    sNZ = sum((n-mean_n)*(z-mean_z) for n,(_,_,z) in zip(nvals,markers))
    det = sEE*sNN-sEN*sEN
    grad_e = (sEZ*sNN-sNZ*sEN)/det
    grad_n = (sNZ*sEE-sEZ*sEN)/det
    residuals = [
        z-(mean_z+grad_e*(e-mean_e)+grad_n*(n-mean_n))
        for n,e,z in markers
    ]
    rms = sqrt(sum(r*r for r in residuals)/len(residuals))
    dip = degrees(atan(hypot(grad_e,grad_n)))
    dip_direction = (degrees(atan2(-grad_e,-grad_n))+360) % 360

    print("\nKHENTKAUS — DIRECT GLSS B01..B10 NATURAL-BEDROCK MARKERS")
    print(f"marker count: {pair(len(markers))}")
    print("marker class: GLSS Table 10, B01..B10, top of lower natural bedrock")
    print(f"mean B-marker datum N/E/Z: {fmt(mean_n,'m')} / {fmt(mean_e,'m')} / {fmt(mean_z,'m')}")
    print(f"provisional convex-hull vertices: {pair(len(hull))}")
    print(f"marker-hull plan area: {fmt(hull_area,'m²',10)}")
    print(f"marker-hull perimeter: {fmt(hull_perimeter,'m')}")
    print(f"marker-hull N/E spans: {fmt(max(nvals)-min(nvals),'m')} / {fmt(max(evals)-min(evals),'m')}")
    print(f"principal marker-axis bearing: {fmt(principal_bearing,'°',1_000_000)}")
    print(f"top-surface fitted-plane dip: {fmt(dip,'°',1_000_000)}")
    print(f"fitted-plane down-dip bearing: {fmt(dip_direction,'°',1_000_000)}")
    print(f"fitted-plane residual RMS: {fmt(rms,'m')}")
    print(f"measured marker-height span: {fmt(max(p[2] for p in markers)-min(p[2] for p in markers),'m')}")
    print("The convex hull is the envelope of ten GLSS markers, not the full geological outcrop boundary or the original parent-mass boundary.")

    # Convert the measured B-marker centroid directly into the local GPMP plane.
    g=gpmp_local()
    kx=mean_e-500000
    ky=mean_n-100000
    khent=(kx,ky)
    print("DISTANCES FROM THE DIRECT GLSS B-MARKER DATUM TO THE PYRAMID CENTRES")
    for name in ("Khufu","Khafre","Menkaure"):
        print(f"{name}--Khentkaus B centroid: {fmt(hypot(khent[0]-g[name][0],khent[1]-g[name][1]),'m')}")

    # Keep the Great Sphinx as a named map-proxy until its local ARCE grid is
    # transformed into GPMP by common control points. Never call this the parent-mass centre.
    kh_lat=MAP_E5["Khufu"][0]/100000
    kh_lon=MAP_E5["Khufu"][1]/100000
    sph_lat=MAP_E5["Great_Sphinx"][0]/100000
    sph_lon=MAP_E5["Great_Sphinx"][1]/100000
    lat0=radians(kh_lat)
    n_per_deg=111132.92
    e_per_deg=111412.84*cos(lat0)-93.5*cos(3*lat0)
    sphinx=(
        (sph_lon-kh_lon)*e_per_deg,
        (sph_lat-kh_lat)*n_per_deg
    )
    khufu=g["Khufu"]
    khafre=g["Khafre"]
    menkaure=g["Menkaure"]
    dA=hypot(sphinx[0]-khufu[0],sphinx[1]-khufu[1])
    dB=hypot(khent[0]-khafre[0],khent[1]-khafre[1])
    lstar=sqrt(dA*dB)
    rel=abs(dA-dB)/((dA+dB)/2)
    print("\nUPDATED CROSS-PAIR DESIGN INVARIANT")
    print("d(P_Khufu, Sphinx-map proxy) = d(P_Khafre, Khentkaus-GLSS B datum) = L*")
    print(f"dA Khufu--Sphinx map proxy: {fmt(dA,'m')}")
    print(f"dB Khafre--Khentkaus measured B datum: {fmt(dB,'m')}")
    print(f"current proxy residual: {fmt(abs(dA-dB),'m')}")
    print(f"relative discrepancy: {fmt(rel,'',1_000_000)}")
    print(f"symmetric ideal length L*=sqrt(dA*dB): {fmt(lstar,'m')}")
    print("The equality itself is exact in the ideal-design layer. The Sphinx endpoint remains a map proxy pending a GPMP/ARCE grid transformation.")

    # Relative positions on the Khufu--Menkaure centre axis.
    vx=menkaure[0]-khufu[0]
    vy=menkaure[1]-khufu[1]
    axis_len=hypot(vx,vy)
    ux,uy=vx/axis_len,vy/axis_len
    px,py=-uy,ux
    def project(point):
        wx,wy=point[0]-khufu[0],point[1]-khufu[1]
        return wx*ux+wy*uy, wx*px+wy*py
    p_khafre=project(khafre)
    p_sphinx=project(sphinx)
    p_khent=project(khent)
    print("\nFIVE-NODE POSITIONS ON THE KHUfu--MENKAURE AXIS")
    for name,pr in (("Khafre",p_khafre),("Sphinx map proxy",p_sphinx),("Khentkaus B centroid",p_khent)):
        print(f"{name}: along={fmt(pr[0],'m')}; cross={fmt(pr[1],'m')}")
    print(f"Sphinx--Khentkaus along-axis gap: {fmt(p_khent[0]-p_sphinx[0],'m')}")
    print(f"Sphinx--Khentkaus cross-axis gap: {fmt(abs(p_khent[1]-p_sphinx[1]),'m')}")
    print(f"Sphinx--Khentkaus direct distance: {fmt(hypot(sphinx[0]-khent[0],sphinx[1]-khent[1]),'m')}")

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
