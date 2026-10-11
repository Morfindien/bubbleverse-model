"""Q-047 M15: offline rational audit of NEW_RECONSTRUCTION fields.
No CLASS load, cosmological integration, fitting, GitHub write or dispatch.
Run from a workspace containing the supplied upload/*.json and raw evidence.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, localcontext
import json, hashlib, datetime, platform

ROOT = Path(__file__).resolve().parent.parent
CASES = ['camspec-lcdm', 'camspec-ede_n3', 'hillipop-lcdm', 'hillipop-ede_n3']

def exact(s):
    return F.from_float(float.fromhex(s))

def rational(x):
    return {'num':str(x.numerator), 'den':str(x.denominator)}

def interval(lo, hi):
    assert lo <= hi
    return {'lo':rational(lo), 'hi':rational(hi)}

def display(x):
    with localcontext() as c:
        c.prec = 22
        return str(Decimal(x.numerator)/Decimal(x.denominator))

def atan_interval(x, terms=80):
    assert 0 < x < 1
    s = sum((-1)**k*x**(2*k+1)/F(2*k+1) for k in range(terms))
    next_term = (-1)**terms*x**(2*terms+1)/F(2*terms+1)
    return min(s,s+next_term), max(s,s+next_term)

def log_positive_interval(x, terms=80):
    assert x > 0
    r=x; e=0
    while r < 1: r*=2; e-=1
    while r >= 2: r/=2; e+=1
    def log_unit(t):
        h=(t-1)/(t+1)
        assert 0 <= h <= F(1,3)
        s=2*sum(h**(2*k+1)/F(2*k+1) for k in range(terms))
        tail=2*h**(2*terms+1)/F(2*terms+1)/(1-h*h)
        return s,s+tail
    ml,mh=log_unit(r); tl,th=log_unit(F(2))
    return (ml+e*tl,mh+e*th) if e>=0 else (ml+e*th,mh+e*tl)

p5=atan_interval(F(1,5)); p239=atan_interval(F(1,239))
pi_lo=16*p5[0]-4*p239[1]; pi_hi=16*p5[1]-4*p239[0]
p2=atan_interval(F(1,2)); p3=atan_interval(F(1,3))
alt_lo=4*(p2[0]+p3[0]);alt_hi=4*(p2[1]+p3[1])
assert max(pi_lo,alt_lo) <= min(pi_hi,alt_hi)
# Exact tangent-addition checks identify both angles with pi/4.
two=2*F(1,5)/(1-F(1,5)**2);four=2*two/(1-two**2)
assert (four-F(1,239))/(1+four*F(1,239))==1
assert (F(1,2)+F(1,3))/(1-F(1,2)*F(1,3))==1

idx=json.loads((ROOT/'upload/Q047_RAW_EVIDENCE_INDEX_V1.json').read_text())
state={}; records={}; links=[]
for case in CASES:
    path=ROOT/f'upload/Q047_RECONSTRUCTION_STATE_{case}_V1.json'
    s=json.loads(path.read_text()); assert s['q']=='Q-047' and s['origin']=='NEW_RECONSTRUCTION' and s['historical_export'] is False
    # Only the sixteen actual mathematical input/source objects are checked here.
    for name in ['accepted_initial_hex.json','effective_background_hex.json','source_objects/source/background.c','source_objects/include/common.h']:
        member=f'q047_reconstructed/{case}/{name}'
        item=next(f for f in idx['files'] if f['artifact_relative_path']==member)
        p=Path(item['local_path']); got=hashlib.sha256(p.read_bytes()).hexdigest();assert got==item['sha256']
        if name in s['raw_member_sha256']: assert got==s['raw_member_sha256'][name]
        if name=='accepted_initial_hex.json':assert json.loads(p.read_text())==s['accepted_initial_hex']
        if name=='effective_background_hex.json':assert json.loads(p.read_text())==s['effective_background_hex']
        links.append({'case':case,'member':member,'sha256':got})
    b=s['effective_background_hex'];a=s['accepted_initial_hex'];v=[exact(x) for x in a['integration_vector']]
    assert exact(b['fields']['H0'])>0 and exact(b['fields']['K'])==0
    assert all(exact(b['fields'][k])>0 for k in ['Omega0_b','Omega0_cdm','Omega0_g','Omega0_ur','T_cmb'])
    assert exact(b['fields']['Omega0_lambda'])>=0
    assert all(b['flags'][k]==0 for k in ['has_idm','has_idr','has_dcdm','has_dr','has_fld','has_curvature'])
    assert exact(a['fields']['a_ini_native'])>0
    assert len(v)==a['bi_size'] and v[a['bi_indices']['D']]==1
    assert b['N_ncdm']==1 and len(b['neutrinos'])==1
    nu=b['neutrinos'][0]; qs=[exact(x) for x in nu['q_ncdm_bg']];ws=[exact(x) for x in nu['w_ncdm_bg']]
    assert len(qs)==len(ws)==11 and all(q>0 for q in qs) and all(w>0 for w in ws)
    assert all(l<r for l,r in zip(qs,qs[1:]))
    assert exact(nu['fields']['M_ncdm'])>0 and exact(nu['fields']['factor_ncdm'])>0
    assert nu['got_files']==0 and exact(nu['fields']['ksi_ncdm'])==0
    if b['scalar'] is not None:
        sc=b['scalar'];par=[exact(x) for x in sc['scf_parameters']]
        assert par[0]==3 and par[1]>0 and par[2]>0 and par[3]>0 and sc['attractor_ic_scf']==0
        assert v[a['bi_indices']['phi']]==exact(a['fields']['phi_ini'])==exact(sc['fields']['phi_ini_scf'])
        assert v[a['bi_indices']['phi_prime']]==exact(a['fields']['phi_prime_ini'])==exact(sc['fields']['phi_prime_ini_scf'])==0
        scalar={'F_eV':display(par[1]),'m_eV':display(par[2]),'B':display(par[3]),'phi_ini':display(v[a['bi_indices']['phi']]),'V_floor_Mpc_minus2':rational(par[3]*F(3968,10**11))}
    else: scalar=None
    state[case]=s
    records[case]={'state_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'positive_nodes':11,'positive_weights':11,'new_initial_vector_index_linkage':'PASS','new_finite_measure_structure':'PASS','new_common_field_positivity':'PASS','scalar':scalar,'historical_PT01':'UNRESOLVED','historical_PT03':'UNRESOLVED','PT04_full':'UNRESOLVED','first_hit':'NOT_COMPUTED','final_result_gate':'UNRESOLVED'}

nu=state[CASES[0]]['effective_background_hex']['neutrinos'][0]
assert all(state[c]['effective_background_hex']['neutrinos'][0]==nu for c in CASES)
assert all(state[c]['accepted_initial_hex']['fields']['a_ini_native']==state[CASES[0]]['accepted_initial_hex']['fields']['a_ini_native'] for c in CASES)
assert all(state[c]['accepted_initial_hex']['fields']['loga_ini']==state[CASES[0]]['accepted_initial_hex']['fields']['loga_ini'] for c in CASES)
qs=[exact(x) for x in nu['q_ncdm_bg']];ws=[exact(x) for x in nu['w_ncdm_bg']]
s3=sum(q**3*w for q,w in zip(qs,ws));s1=sum(q*w for q,w in zip(qs,ws));nn=exact(nu['fields']['factor_ncdm']);mass=exact(nu['fields']['M_ncdm'])
source_pi=F('3.1415926535897932384626433832795')
ideal_fd_lo=7*pi_lo/480;ideal_fd_hi=7*pi_hi/480
fd_lo=7*pi_lo**4/(480*source_pi**3);fd_hi=7*pi_hi**4/(480*source_pi**3);gap_lo=fd_lo-s3;gap_hi=fd_hi-s3
assert gap_lo>0
rel_lo=gap_lo/fd_hi;rel_hi=gap_hi/fd_lo
ai=exact(state[CASES[0]]['accepted_initial_hex']['fields']['a_ini_native']);ui=exact(state[CASES[0]]['accepted_initial_hex']['fields']['loga_ini'])
# Positive-mass corrections: sqrt(q^2+mu^2)-q <= mu^2/(2q).
finite_correction=mass**2*ai**2*s1/2
fd_correction_hi=mass**2*ai**2*pi_hi**2/(96*source_pi**3)
full_gap_lo=gap_lo-finite_correction;full_gap_hi=gap_hi+fd_correction_hi
assert full_gap_lo>0
rho_gap_lo=nn*ai**-4*full_gap_lo;rho_gap_hi=nn*ai**-4*full_gap_hi
log_lo,log_hi=log_positive_interval(ai);du_lo=ui-log_hi;du_hi=ui-log_lo
assert du_hi<0
# With d=-delta_u>0, d/(1+d) <= 1-exp(-d) <= d.
dlo=-du_hi;dhi=-du_lo;relative_a_lo=dlo/(1+dlo);relative_a_hi=dhi

result={'schema':'Q047_M15_EXACT_AUDIT_V1','q':'Q-047','case_id':'NOT_DOCUMENTED','result_id':'R-PROPOSED-Q047-M15-001','run_id':'38140371059','origin':'NEW_RECONSTRUCTION','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':platform.python_version(),'method':'Standard-library Fraction rational arithmetic; alternating arctangent and positive atanh logarithm remainder bounds. No native CLASS execution.','rounding_or_uncertainty':'Exact binary64 values are decoded to rationals; deterministic numerical reference bounds, not statistical/physical parameter errors.','cases':records,'controls':{'actual_source_and_state_hashes':16,'two_pi_formulas_exact_tangent_and_overlapping_intervals':True,'all_four_neutrino_objects_identical':True,'all_four_a_loga_bits_identical':True,'strictly_positive_massless_and_actual_initial_density_gap':True,'strictly_negative_initial_coordinate_delta':True},'pi_enclosure':interval(pi_lo,pi_hi),'massless_moments':{'finite_S3':rational(s3),'source_PI_exact_decimal':rational(source_pi),'FD_definition':'1/[4*pi_source^3*(exp(q)+1)], pi_source is the exact pinned decimal macro; mathematical pi appears in analytic integrals. Native generation arithmetic is a distinct relation.','ideal_mathematical_pi_FD_S3':interval(ideal_fd_lo,ideal_fd_hi),'FD_S3':interval(fd_lo,fd_hi),'FD_minus_finite':interval(gap_lo,gap_hi),'relative_gap_wrt_FD':interval(rel_lo,rel_hi),'relative_gap_display':[display(rel_lo),display(rel_hi)]},'positive_mass_initial_density':{'a_native_exact':rational(ai),'M_exact':rational(mass),'factor_exact':rational(nn),'rho_FD_minus_rho_finite_Mpc_minus2':interval(rho_gap_lo,rho_gap_hi),'gap_display_Mpc_minus2':[display(rho_gap_lo),display(rho_gap_hi)],'scope':'Exact-real finite-node versus source-decimal-PI analytic xi=0 FD reference, same captured normalization/mass/closure, at captured NEW native a_ini only. Not compiled-source rounding or an event certificate.'},'initial_coordinate':{'native_u_exact':rational(ui),'ln_native_a':interval(log_lo,log_hi),'u_native_minus_ln_a_native':interval(du_lo,du_hi),'delta_u_display':[display(du_lo),display(du_hi)],'one_minus_exp_u_over_native_a':interval(relative_a_lo,relative_a_hi),'scope':'Native log(a) is a distinct rounded coordinate; a_hat and u_hat cannot simultaneously be imposed as exact-real a=exp(u). Define source-real initialization at a_hat, carry this offset for a claimed compiled-path relation.'},'first_unsupported_historical_primitive':'Original accepted Theta and initial realization equivalence or complete validated inverse. Exact output equality does not discharge it.','native_processes_started':0,'cmb_or_likelihood_evaluations':0,'repository_writes':0,'workflow_dispatches':0,'scientific_verdict':'INSUFFICIENT_EVIDENCE','final_result_gate':'UNRESOLVED','sources':links}
(ROOT/'q047_math_work/Q047_M15_EXACT_AUDIT_V1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'controls':result['controls'],'relative_massless_gap':result['massless_moments']['relative_gap_display'],'initial_density_gap':result['positive_mass_initial_density']['gap_display_Mpc_minus2'],'delta_u':result['initial_coordinate']['delta_u_display'],'cases':records},indent=2))

