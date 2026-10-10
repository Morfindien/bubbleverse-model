"""Q044 bounded component computation; no production, no posterior inference.
Run: python Q044_SPLINE_ADJOINT.py [INPUTS.json] [RESULT.json]
Targets exact-real arithmetic at decoded binary64 knots, not CLASS rounding error.
"""
import json, sys, math, hashlib, platform, time
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from q042_interval_v29 import I, VERSION

def point(a):
    a=np.asarray(a,dtype=float); return a,a
def add(a,b): return np.nextafter(a[0]+b[0],-np.inf),np.nextafter(a[1]+b[1],np.inf)
def neg(a): return -a[1],-a[0]
def sub(a,b): return add(a,neg(b))
def mul(a,b):
    v=np.array([a[i]*b[j] for i in (0,1) for j in (0,1)])
    return np.nextafter(v.min(axis=0),-np.inf),np.nextafter(v.max(axis=0),np.inf)
def div(a,b):
    if np.any((b[0]<=0)&(b[1]>=0)): raise ValueError('zero denominator')
    v=np.array([a[i]/b[j] for i in (0,1) for j in (0,1)])
    return np.nextafter(v.min(axis=0),-np.inf),np.nextafter(v.max(axis=0),np.inf)
def isum(a):
    lo,hi=map(lambda v:np.asarray(v).ravel(),a)
    while len(lo)>1:
        if len(lo)%2: lo=np.append(lo,0.);hi=np.append(hi,0.)
        lo,hi=add((lo[::2],hi[::2]),(lo[1::2],hi[1::2]))
    return float(lo[0]),float(hi[0])
def thomas(diag,off,rhs):
    d=diag.copy();r=rhs.copy()
    for i in range(1,len(d)):
        q=off[i-1]/d[i-1];d[i]-=q*off[i-1];r[i]-=q*r[i-1]
    r[-1]/=d[-1]
    for i in range(len(d)-2,-1,-1): r[i]=(r[i]-off[i]*r[i+1])/d[i]
    return r
def transpose_B(lam,h):
    qlo=np.zeros(len(h[0]));qhi=qlo.copy()
    qlo[1:],qhi[1:]=mul(point(6), (lam[0][1:-1],lam[1][1:-1]))
    v=mul(point(-6),(lam[0][1:-1],lam[1][1:-1]))
    qlo[:-1],qhi[:-1]=add((qlo[:-1],qhi[:-1]),v)
    for j,k,li in [(0,1,0),(-1,-2,-1)]:
        fac=div(mul(point(6),(h[0][j],h[1][j])),add((h[0][j],h[1][j]),(h[0][k],h[1][k])))
        v=mul(fac,(lam[0][li],lam[1][li]))
        qlo[j],qhi[j]=sub((qlo[j],qhi[j]),v) if j==0 else add((qlo[j],qhi[j]),v)
        qlo[k],qhi[k]=add((qlo[k],qhi[k]),v) if j==0 else sub((qlo[k],qhi[k]),v)
    q=div((qlo,qhi),h)
    zlo=np.zeros(len(h[0])+1);zhi=zlo.copy()
    zlo[:-1],zhi[:-1]=neg(q)
    zlo[1:],zhi[1:]=add((zlo[1:],zhi[1:]),q)
    return zlo,zhi
def weights(x,sign=1):
    n=len(x)
    if n<3 or not np.all(np.diff(x)<0): raise ValueError('require >=3 descending knots')
    h=sub(point(x[1:]),point(x[:-1]));hc=np.diff(x)
    diag=np.r_[2*hc[0],2*(hc[:-1]+hc[1:]),2*hc[-1]]
    hh=mul(mul(h,h),h);piece=div(hh,point(24))
    clo=np.zeros(n);chi=clo.copy();clo[:-1],chi[:-1]=piece
    clo[1:],chi[1:]=add((clo[1:],chi[1:]),piece)
    cc=np.zeros(n);cc[:-1]=hc**3/24;cc[1:]+=hc**3/24
    lam=thomas(diag,hc,cc)
    dl=np.empty(n);du=np.empty(n)
    dl[0],du[0]=mul(point(2),(h[0][0],h[1][0]));dl[-1],du[-1]=mul(point(2),(h[0][-1],h[1][-1]))
    dl[1:-1],du[1:-1]=mul(point(2),add((h[0][:-1],h[1][:-1]),(h[0][1:],h[1][1:])))
    prod=mul((dl,du),point(lam))
    v=mul(h,point(lam[1:]));prod=(prod[0].copy(),prod[1].copy());prod[0][:-1],prod[1][:-1]=add((prod[0][:-1],prod[1][:-1]),v)
    v=mul(h,point(lam[:-1]));prod[0][1:],prod[1][1:]=add((prod[0][1:],prod[1][1:]),v)
    residual=sub((clo,chi),prod)
    # For same-sign h, diagonal dominance margins are |h0|, |hprev+hnext|, |hlast|.
    delta=float(np.min(-h[1])) # safe lower bound for every margin
    rmax=float(np.max(np.maximum(abs(residual[0]),abs(residual[1]))))
    err=float(div(point(rmax),point(delta))[1])
    lint=add(point(lam),(-err,err))
    bt=transpose_B(lint,h)
    tlo=np.zeros(n);thi=tlo.copy();v=div(h,point(2));tlo[:-1],thi[:-1]=v
    tlo[1:],thi[1:]=add((tlo[1:],thi[1:]),v)
    w=sub(neg((tlo,thi)),mul(point(sign),bt))
    if not all(np.isfinite(a).all() for a in w):raise ValueError('nonfinite')
    return w,{'lambda_error_bound':err,'residual_bound':rmax,'dominance_lower_bound':delta}

def rational_direct(x,y,sign=1):
    # Independently form full forward spline matrix and eliminate exactly.
    x=[F(v.item() if isinstance(v,np.generic) else v) for v in x];y=[F(v.item() if isinstance(v,np.generic) else v) for v in y];n=len(x);h=[x[i+1]-x[i] for i in range(n-1)]
    d=[(y[i+1]-y[i])/h[i] for i in range(n-1)]
    slopes=[d[0]-h[0]*(d[1]-d[0])/(h[0]+h[1]),d[-1]+h[-1]*(d[-1]-d[-2])/(h[-2]+h[-1])]
    A=[[F(0) for _ in x] for _ in x];b=[F(0) for _ in x]
    A[0][0]=2*h[0];A[0][1]=h[0];b[0]=6*(d[0]-slopes[0])
    for i in range(1,n-1):A[i][i-1]=h[i-1];A[i][i]=2*(h[i-1]+h[i]);A[i][i+1]=h[i];b[i]=6*(d[i]-d[i-1])
    A[-1][-2]=h[-1];A[-1][-1]=2*h[-1];b[-1]=6*(slopes[1]-d[-1])
    for k in range(n):
        for i in range(k+1,n):
            q=A[i][k]/A[k][k]
            for j in range(k,n):A[i][j]-=q*A[k][j]
            b[i]-=q*b[k]
    m=[F(0) for _ in x]
    for i in range(n-1,-1,-1):m[i]=(b[i]-sum(A[i][j]*m[j] for j in range(i+1,n)))/A[i][i]
    return -sum(h[i]*(y[i]+y[i+1])/2+sign*h[i]**3*(m[i]+m[i+1])/24 for i in range(n-1))
def checks():
    rng=np.random.default_rng(44044);count=0;maxwidth=0
    for n in range(3,11):
        for k in range(4):
            x=np.r_[0.,-np.cumsum(rng.integers(1,15,size=n-1))];y=rng.integers(-20,20,size=n)
            for sign in (1,-1):
                w,_=weights(x,sign)
                for j in range(n):
                    v=[0]*n;v[j]=1;r=rational_direct(x,v,sign)
                    assert F(float(w[0][j]))<=r<=F(float(w[1][j])),(n,j,sign)
                r=rational_direct(x,y,sign);b=isum(mul(w,point(y)))
                assert F(b[0])<=r<=F(b[1]);maxwidth=max(maxwidth,b[1]-b[0]);count+=1
    for degree in range(3):
        x=[8,5,2,0];y=[v**degree for v in x]
        assert rational_direct(x,y,-1)==F(8**(degree+1),degree+1)
    assert rational_direct([2,1,0],[4,1,0],1)==F(10,3)
    assert rational_direct([2,1,0],[4,1,0],-1)==F(8,3)
    return {'status':'PASS','exact_rational_fixture_cases':count,'quadratic_native_plus':'10/3','quadratic_cubic_minus':'8/3','max_fixture_enclosure_width':maxwidth,'seed':44044}

def boxes(inp,cert):
    c={k:I(float.fromhex(v)) for k,v in inp['constants'].items()};p={k:I(float.fromhex(v)) for k,v in inp['trials'][cert['trial']].items()}
    rail=I(*map(float.fromhex,cert['xH_rail_hex']));witness={w['index']:I(*map(float.fromhex,w['xe_source_bounds']['binary64_hex_bounds'])) for w in cert['witnesses']}
    ys=[];xs=[];xe=[]
    for idx,row in enumerate(inp['grid_rows']):
        z0=float.fromhex(row[0]);z=I(z0);xs.append(float.fromhex(row[1]))
        if z0>50: raise ValueError('grid scope > entry')
        if z0<=float(p['start'].lo):
            arg=((1+p['center']).power(1.5)-(1+z).power(1.5))/(p['exponent']*(1+p['center']).power(.5)*p['width'])
            f=(1+arg.tanh())/2;he=p['he_fraction']*(1+((p['he_center']-z)/p['he_width']).tanh())/2
        else:f=I(0);he=I(0)
        if z0<=46:q=I(1)
        else:s=(50-z)/4;q=s*s*(3-2*s)
        beta=(1-q*f).intersect(0,1)
        if beta is None:raise ValueError('beta domain')
        val=beta*(rail+c['fHe']*c['helium'])+q*(f*p['after']+he)
        if idx in witness:
            val=val.intersect(witness[idx].lo,witness[idx].hi)
            if val is None:raise ValueError('empty witness intersection')
        xe.append(val.pair());ys.append(((1+z)*(1+z)*c['nH0']*c['sigma']*c['Mpc']*val).pair())
    return np.array(xs),np.array(ys).T,np.array(xe)
def main():
    start=time.time();ip=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).with_name('Q044_SPLINE_INPUTS.json'));inp=json.loads(ip.read_text())
    tests=checks();out={'q':'Q044','case_id':'NOT DOCUMENTED','result_id':'R-Q044-SPLINE-ADJOINT-001','result_type':'CONDITIONAL_MATHEMATICAL_COMPONENT_RESULT','target':inp['target'],'production_restart_authorized':False,'tests':tests,'trials':[],'environment':{'python':platform.python_version(),'numpy':np.__version__,'MPFR':VERSION},'input_sha256':hashlib.sha256(ip.read_bytes()).hexdigest(),'source_hashes':inp['source_hashes']}
    for cert in inp['trials_certificate']:
        x,y,xe=boxes(inp,cert);cells=[]
        for support in cert['candidate_indices']:
            if support==0:cells.append({'support':0,'N':0,'tau_bounds':[0.,0.]});continue
            n=max(3,support);w,meta=weights(x[:n],1);bound=isum(mul(w,(y[0,:n],y[1,:n])))
            cells.append({'support':support,'N':n,'tau_bounds':list(bound),'max_weight_interval_width':float(np.max(w[1]-w[0])),**meta})
        lower=min(cells,key=lambda a:a['tau_bounds'][0]);upper=max(cells,key=lambda a:a['tau_bounds'][1]);bounds=[lower['tau_bounds'][0],upper['tau_bounds'][1]]
        out['trials'].append({'trial':cert['trial'],'support_count':len(cells),'support_hull_bounds':bounds,'width':bounds[1]-bounds[0],'lower_support':lower['support'],'upper_support':upper['support'],'source_box_method':'inherited global hydrogen rail intersected with 33 retained source-xe witnesses; MPFR outward affine source evaluation','source_xe_boxes_hex':[[float(v).hex() for v in row] for row in xe],'dkappa_boxes_hex':[[float(y[0,i]).hex(),float(y[1,i]).hex()] for i in range(len(x))],'support_cells':cells,'qualification':'conditional enclosure of frozen native-plus exact-real spline component only; not a qualified tau/posterior/reference'})
        print(cert['trial'],bounds,len(cells),flush=True)
    out['elapsed_seconds']=time.time()-start;out['accuracy_requirement']='NOT AVAILABLE';out['inference_adequacy']='UNDETERMINED';out['binary64_native_rounding_error']='NOT CERTIFIED';out['complete_V31_history_recovered']=False
    op=Path(sys.argv[2] if len(sys.argv)>2 else Path(__file__).with_name('Q044_SPLINE_RESULT.json'));op.write_text(json.dumps(out,indent=2)+'\n');print(tests,flush=True)
if __name__=='__main__':main()
