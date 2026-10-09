"""Finite Q044 verification, separate from inference qualification.
Compile: gcc -shared -fPIC -O0 -fno-fast-math -ffp-contract=off Q044_NATIVE_REPLAY.c -o native_replay.so
Run: python Q044_SPLINE_VALIDATE.py [path/to/native_replay.so]
"""
import ctypes as C,json,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
from Q044_SPLINE_ADJOINT import weights,mul,point,isum,rational_direct,checks
root=Path(__file__).parent
lib=C.CDLL(str(Path(sys.argv[1] if len(sys.argv)>1 else root/'native_replay.so').resolve()))
lib.q044_replay.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_int];lib.q044_replay.restype=C.c_double
def replay(x,y):
    x=np.ascontiguousarray(x,dtype=np.float64);y=np.ascontiguousarray(y,dtype=np.float64)
    return lib.q044_replay(x.ctypes.data_as(C.POINTER(C.c_double)),y.ctypes.data_as(C.POINTER(C.c_double)),len(x))
inp=json.loads((root/'Q044_SPLINE_INPUTS.json').read_text());result=json.loads((root/'Q044_SPLINE_RESULT.json').read_text())
x=np.array([float.fromhex(row[1]) for row in inp['grid_rows']]);cases=[]
for t in result['trials']:
    y=np.array([[float.fromhex(v) for v in row] for row in t['dkappa_boxes_hex']]);supports=sorted(set([t['support_cells'][0]['support'],t['support_cells'][len(t['support_cells'])//2]['support'],t['support_cells'][-1]['support']]))
    for support in supports:
        n=max(3,support)
        w,_=weights(x[:n]);wm=(w[0]+w[1])/2
        yy=y[:n]
        for name,ord in [('midpoint',(yy[:,0]+yy[:,1])/2),('min_sign_vertex',np.where(wm>=0,yy[:,0],yy[:,1])),('max_sign_vertex',np.where(wm>=0,yy[:,1],yy[:,0]))]:
            exactreal=isum(mul(w,point(ord[:n])));native=replay(x[:n],ord[:n]);gap=max(exactreal[0]-native,native-exactreal[1],0.)
            # Component diagnostic tolerance only; does not certify native rounding globally.
            tolerance=1e-9*max(1.,abs(native));assert gap<=tolerance
            assert t['support_hull_bounds'][0]-tolerance<=native<=t['support_hull_bounds'][1]+tolerance
            cases.append({'trial':t['trial'],'support':support,'ordinate':name,'native_binary64_value':native,'exact_real_enclosure':list(exactreal),'outside_enclosure_distance':gap,'diagnostic_tolerance':tolerance})
assert abs(replay([2.,1.,0.],[4.,1.,0.])-10/3)<1e-14
# This is a deliberate native+ versus mathematical cubic− witness, not an implementation change.
weightchange=max(abs(((weights(x[:3195])[0][0]+weights(x[:3195])[0][1])/2)-((weights(x[:3332])[0][0][:3195]+weights(x[:3332])[0][1][:3195])/2)))
assert weightchange>0
out={'q':'Q044','validation_id':'I-Q044-SPLINE-CHECKS-001','status':'PASS_COMPONENT_SCOPE_ONLY','rational_checks':checks(),'native_replay_cases':cases,'max_native_replay_gap':max(c['outside_enclosure_distance'] for c in cases),'prefix_weight_change_max':float(weightchange),'support_coverage':[{'trial':t['trial'],'expected':len(c['candidate_indices']),'actual':len(t['support_cells']),'exact_index_set_match':c['candidate_indices']==[v['support'] for v in t['support_cells']]} for c,t in zip(inp['trials_certificate'],result['trials'])],'compile_flags':'-shared -fPIC -O0 -fno-fast-math -ffp-contract=off','compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'hashes':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['Q044_SPLINE_INPUTS.json','Q044_SPLINE_ADJOINT.py','Q044_NATIVE_REPLAY.c','q042_interval_v29.py','Q044_SPLINE_RESULT.json']},'limitations':['native floating execution diagnostic is not a proved uniform binary64 rounding-error enclosure','V31 full raw node histories absent','no physical downstream inference qualification','no production authorized or executed']}
assert all(c['exact_index_set_match'] for c in out['support_coverage'])
(root/'Q044_SPLINE_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(cases),out['max_native_replay_gap'],weightchange)
