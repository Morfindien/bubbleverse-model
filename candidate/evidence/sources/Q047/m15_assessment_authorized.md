# BUBBLEVERSE — Q047 M15: finite admission assessment of the actual reconstructed state

DATE AND TIME UTC: 2026-10-11T13:30:30.170258+00:00
DATE AND TIME Europe/Copenhagen: 2026-10-11T15:30:30.170258+02:00
STATUS: CONTINUES — the M15 assessment is complete; the exact Q is unresolved.
CURRENT Q: Q-047
CASE ID: NOT DOCUMENTED; unchanged.
QUESTION: For each of the four frozen Q041 diagnostic FULL/start0 LCDM and n_scf=3 EDE configurations, does the qualified pre-cutoff helium-recombination trajectory reach q=xHeII=10^-6 at a finite first event with a strictly negative upper-branch rate and no competing switch or reset?
SELECTED NEXT ENGINE: Existing RESULT INGESTION & ROUTING ENGINE.
ACTIVE ROUTING: Integrate the finite M15 result and precise contract-admission limit. No native replay, generic search, unchanged M14/M15 repetition or automatically authorized next campaign.

## J-PROPOSED-Q047-M15 — newly instantiated finite measure and source-real initialization distinctions

RESULT ID: R-PROPOSED-Q047-M15-001.
INTERNAL SOURCE ID: I-PROPOSED-Q047-M15-001.
SOURCE TYPE: Bubbleverse-generated mathematical/technical evidence, using the actual NEW_RECONSTRUCTION objects from run 38140371059, attempt 1, commit 76d6b4a4b02ddd929899008f476e99da29c1f931. No new external scientific publication or scientific Q.

[KEEP / CONTINUITY] The complete inherited 3,339,404-byte journal follows verbatim after this differential entry and its reproducibility objects. Parent SHA256: df367942c93f7fa100951363bcf9221064b874d0a4ff74dc3b882d7f74fd863d. This preserves M01–M14, every existing K/I/R ID, previous failures, rejected routes, raw results, contracts and sources. The complete supplied handoff and all ten attachment contents were read locally; their declared prior-delivery hashes match. Their validation receipt is reused as technical evidence, not treated as a physics certificate.

[ADD / ACTUAL INPUT QUALIFICATION] Sixteen relevant state/source objects were hash-checked: accepted initial state, effective background, background.c and common.h for each case. The four compact state views equal the corresponding raw JSON objects. All four new realizations have exactly eleven strictly positive, strictly increasing neutrino momenta and eleven strictly positive effective weights. Their neutrino objects, including mass M, normalization N, temperature ratio, degeneracy, xi=0 and no-distribution-file flag, are identical. The initial a and loga bit patterns are also identical across cases. A weight is an effective integration weight, not a probability; no invented sum-to-one normalization is imposed.

The new accepted scalar coordinates agree exactly with the exported integration-vector indices and effective scalar fields. Both EDE cases have n=3, non-attractor initial conditions, F>0, m>0, B>0 and phi_prime_ini=0. All four common density coefficients needed below are positive, K=0 and the omitted background component flags are zero. This establishes the checked representation/index/positivity subclaims for NEW_RECONSTRUCTION only. It does not set original PT01/PT03, PT02 or complete PT04 to PASS.

| New case | F [eV], display approximation | m [eV], display approximation | B, dimensionless | accepted phi_ini, reduced-Planck units |
|---|---:|---:|---:|---:|
| camspec-ede_n3 | 1.906128e26 | 1.957352e-27 | 2.672689 | 0.2288527381 |
| hillipop-ede_n3 | 1.944098e26 | 1.249900e-27 | 2.739601 | 0.2355272502 |

These are decoded native parameter representations, not fits, posterior uncertainties or measurements of the Universe. Exact hexadecimal inputs and rational values remain in the preserved state objects/control artifact. In particular, the requested placeholder scf_parameters array is not substituted for these post-shooting fields.

### M15.1 — exact-real candidate and dimensions

Let a be dimensionless, u=ln(a), H in Mpc^-1, and all CLASS-normalized densities/pressures in Mpc^-2. Define N as the exact rational decoded from factor_ncdm, M from M_ncdm, and q_i,w_i from the captured binary64 arrays. They are fixed inputs of a separately tagged finite-node candidate, not uncertain physical parameters.

    epsilon_i(a) = sqrt(q_i^2 + M^2*a^2)
    rho_Q(a) = N*a^-4*sum_i w_i*q_i^2*epsilon_i(a)
    p_Q(a) = N*a^-4/3*sum_i w_i*q_i^4/epsilon_i(a).

There is no repeated Fermi–Dirac weighting: w_i already contains the distribution contribution. The source functions background_ncdm_momenta and background_functions support the kernel and normalization mapping. Rounding of the compiled z=1/a-1, pow, multiplication and sqrt paths is a separate forward relation; the above exact-real formula is not claimed to equal the compiled output without error.

For LCDM, use the unchanged source-real background equation in the precursor contract with the captured H0 and Omega coefficients. For EDE, use the same equation plus

    V(phi) = C*m^2*F^2*[1-cos(kappa*phi/F)]^3 + b0*B
    C = 4152.39, kappa = 2.435e27 eV, b0 = 3.968e-8 in the pinned unit convention
    X = phi_prime/a
    phi_u = X/H,  X_u = -3*X - V_phi/H
    rho_scf = (X^2/2+V)/3, p_scf = (X^2/2-V)/3.

Here phi is dimensionless in reduced-Planck units, phi_prime and X have Mpc^-1 units, F and m are eV, and V has the Mpc^-2 numerical convention after factoring out reduced-Planck mass squared. C and b0 carry the pinned conversion units. Their decimal definitions are fixed model constants, not tunable conversion factors. No recomputation of Lambda, B, M or N absorbs the finite-node/continuous-reference difference.

[DERIVED / SCOPED REGULARITY] Positivity of the actually captured q_i,w_i,N,M instantiates the retained M14 finite-measure assumptions for this new candidate. For a>0, rho_Q>0 and p_Q>0,

    rho_Q - 3*p_Q = N*M^2*a^-2*sum_i w_i*q_i^2/epsilon_i > 0
    d rho_Q/d ln(a) = -3*(rho_Q+p_Q).

Thus 0<3p_Q<rho_Q, and the retained M14 monotone forcing bounds apply to the exact-real finite-node realization. This is stronger than the earlier conditional statement that weight positivity and realized nodes had not been supplied. It is not an all-realizations/historical error certificate.

The new LCDM candidate has H^2>0 on a>0 because the radiation/matter/neutrino contributions are positive. For each new EDE candidate, V>=b0*B>0, hence H^2>=b0*B/3>0. The two-state vector field is locally smooth at finite phi,X and a>0. Its energy E=X^2/2+V satisfies E_u=-3X^2. Starting from the declared new initial state, E cannot increase forward; X is bounded by its initial energy and phi_u remains bounded on every finite u interval. This excludes finite-u blow-up for this reduced exact-real background equation. It does not certify the source-active latch V_e/(3H^2)<0.5, thermodynamics, source error latches, native integration error, historical identity or any helium event. PT05 remains UNRESOLVED.

### M15.2 — source/ideal FD references are distinct from the actual finite rule

The captured flags select an analytic xi=0 distribution, not a distribution file. Preserve the pinned macro

    pi_s = 3.1415926535897932384626433832795

as an exact decimal when defining a source-decimal exact-real reference. Let pi denote mathematical pi. This distinguishes source-literal, compiled binary64 and ideal mathematical constants rather than silently replacing one by another.

    f_s(q) = 1/[4*pi_s^3*(exp(q)+1)]
    S3_s = integral_0^infinity q^3*f_s(q)dq = 7*pi^4/(480*pi_s^3)
    S1_s = integral_0^infinity q*f_s(q)dq = pi^2/(48*pi_s^3).

For the separately named ideal mathematical-pi FD reference, S3_FD=7*pi/480 and S1_FD=1/(48*pi). The expansions 1/(e^q+1)=sum_{k>=1}(-1)^(k-1)e^(-kq), followed by integrating q^3 and q, give these expressions using the alternating zeta sums. Absolute integrability of the summed integrated terms justifies interchange. The Wolfram symbolic control independently returns {7*pi/480,1/(48*pi),0}, where zero is the density/pressure conservation identity. The source-decimal version follows by the explicit normalization ratio (pi/pi_s)^3. No native FD-generation arithmetic/error assumption is added.

Using exact decoded nodes and weights,

    S3_Q = sum_i w_i*q_i^3 approximately 0.04581473885117927
    S3_s approximately 0.04581489286485115
    (S3_s-S3_Q)/S3_s approximately 3.36165e-6 = 3.36165 ppm, strictly positive.

Exact rational arctangent intervals bound pi; the lower and upper discrepancy bounds remain positive. The number is a deterministic massless-limit quadrature/reference discrepancy for this particular new finite rule and the same fixed normalization. It is not a physical uncertainty, compiled-code ULP bound, total cosmological-density error, result for all redshifts or event-location error. The ideal-pi comparison is separately recorded and has the same displayed six significant digits.

[DERIVED / ACTUAL POSITIVE-MASS INITIAL POINT] The actual captured M is positive. The inequality

    0 <= sqrt(q^2+mu^2)-q <= mu^2/(2q), q>0

transfers the massless calculation to the captured new a_ini without pretending that M=0. With mu=M*a and S1_Q=sum_i w_i*q_i,

    rho_s(M,a)-rho_Q(M,a) >= N*a^-4*[S3_s-S3_Q - (M*a)^2*S1_Q/2]
    rho_s(M,a)-rho_Q(M,a) <= N*a^-4*[S3_s-S3_Q + (M*a)^2*pi^2/(96*pi_s^3)].

Both endpoints were evaluated outward at the exact captured a_ini, about 1e-14. The lower bound is strictly positive; the density difference is approximately 2.12843e38 Mpc^-2 in CLASS H^2-normalized units at that initial point. The large dimensional value reflects the a^-4 early-time scale. It establishes that even with the actual nonzero mass, these two exact-real reference forcings cannot be called identical at this point. It is not an observed cosmological discrepancy or a bound at helium recombination. The full precursor-domain quadrature/error certificate is not supplied, and PT04 remains UNRESOLVED.

### M15.3 — the rounded initial coordinate is a separate mathematical object

All four actual captures give

    a_hat = exact value of 0x1.6849b86a12b9bp-47
    u_hat = exact value of -0x1.01e3b843eaa73p+5.

The source sets *loga_ini=log(a) after computing the accepted state at a. An exact rational atanh-series enclosure proves

    delta_u = u_hat - ln(a_hat) approximately -1.26152e-15, strictly negative.

Consequently a_hat and u_hat cannot simultaneously be imposed as exact-real values satisfying a=exp(u). This is a documented deterministic coordinate-rounding relation, not a bug or failed initialization. A candidate using the captured physical scale factor initializes at u0=ln(a_hat); a claimed relation to the compiled integration beginning at u_hat must carry delta_u. Alternatively, a reference that starts at u_hat must explicitly propagate the scale-factor/initial-state change. Do not silently replace either native value.

For d=-delta_u>0,

    d/(1+d) <= 1-exp(u_hat)/a_hat <= d.

This follows from e^d>=1+d and e^(-d)>=1-d. It supplies a finite conservative coordinate bound using no unproved native log/exp error constant. It does not relate the accepted NEW state to the original historical accepted state.

### M15.4 — original-case admission remains the first unsupported primitive

[MATHEMATICAL LOGIC] Let A be the preserved historical archive, O(Theta,E) the numerical output map with its environment E, and C(A) a rigorously complete enclosure of source-real realizations compatible with A under justified source/output errors. The actual equality O_new=A demonstrates reproduction by this NEW numerical run. It does not prove historical Theta_new=Theta_old or that a proposed source-real C(A) is complete.

Uniqueness is not required unnecessarily: a non-singleton C(A) can suffice if it contains the actual realization and the same event verdict is certified for every retained realization. The missing primitive is either attributable historical state/equivalence linkage, or a justified historical forward-output relation plus complete inverse covering every compatible accepted initialization. The new native witness and ideal once-rounded M12 boxes do not supply that universal statement. No actual counterexample to injectivity, no theorem of impossibility and no physical falsification is asserted.

The new library bytes, six FP checkpoints and dlsym reference addresses remain useful new-run evidence. They do not establish the original worker's all-call FP/GOT relation or a domain-specific historical cos/sincos/pow error enclosure. No eta_j is guessed, and no compiled arithmetic path is replaced by one final rounding. These are genuine remaining obligations, not a repeated request to acquire the successful new snapshots.

| Case | New finite-measure/index/positivity subclaims | Original PT01 | Original PT03 | Full PT04 | First hit / final result |
|---|---|---|---|---|---|
| camspec-lcdm | PASS within stated scope | UNRESOLVED | UNRESOLVED | UNRESOLVED | NOT COMPUTED / UNRESOLVED |
| camspec-ede_n3 | PASS within stated scope | UNRESOLVED | UNRESOLVED | UNRESOLVED | NOT COMPUTED / UNRESOLVED |
| hillipop-lcdm | PASS within stated scope | UNRESOLVED | UNRESOLVED | UNRESOLVED | NOT COMPUTED / UNRESOLVED |
| hillipop-ede_n3 | PASS within stated scope | UNRESOLVED | UNRESOLVED | UNRESOLVED | NOT COMPUTED / UNRESOLVED |

[REFINE / WHAT CHANGED] The new discrete measure's positivity and common realization are established, the new accepted scalar index linkage is checked, exact-real background regularity is derived within the stated reduced model, and two actual deterministic reference/coordinate differences are bounded. The earlier absence of NEW nodes/weights/initial vectors is superseded. Historical absence and incomplete error/inverse linkage remain separate.

[KEEP / WHAT DID NOT CHANGE] Exact Q, CASE status, four requested configurations, original core/source/contract hashes, scientific threshold, source switches, all prior conditional mathematical results and falsified/rejected methods. All four scientific verdicts remain INSUFFICIENT_EVIDENCE; PT01/PT03 and FINAL_RESULT_GATE remain UNRESOLVED. No first hit, nonreachability, optical-depth bias, CMB/likelihood effect, H0 shift or model preference is inferred. No physical anomaly is established by the two explicitly derived implementation/reference differences.

[ACCOUNTING] New native CLASS processes, CMB/likelihood evaluations, GitHub writes and workflow dispatches in M15: zero. The small exact-rational arithmetic audit and independent symbolic checks are actual mathematical computation, not a native cosmological campaign. Inherited ledger 16/52 used, 36 remaining is unchanged. The completed reconstruction's separate four-process/28-internal-entry ledger is preserved. No new runnable GitHub target, registry entry, workflow or PROGRAM_ID is introduced.

[STOP / NO LOOP] The finite mathematical task is complete at the first unsupported historical admission primitive. Additional unchanged acquisition, old inventory searches, M14 disassembly or M15 arithmetic replay has no justified information gain. Return this result to the established Result Ingestion & Routing Engine for integration and contract-feasibility assessment. Resume specialist mathematics only for a specific new attributable historical/equivalence object or a genuinely justified forward-error/inverse primitive; there is no automatic new campaign. A separately authorized scoped reconstructed first-event certificate would remain separate from the original historical answer until linkage is established. No target/contract amendment is made here.

[Q-COMPLETION GATE] NOT YET SATISFIED: no admitted original precursor/onset/event packet exists, and a concrete missing identity/error relation could materially alter the answer. Completion of the finite admission assessment is not closure of the exact scientific Q. If later integration establishes a defensible sufficiently documented answer, stop investigation and send the full case directly to MOTOR 14. Report Writer is excluded.

### Source register and claim map — additions, existing IDs retained

I-PROPOSED-Q047-M15-001: Bubbleverse Mathematical Engine, 2026, “Finite assessment of Q047 run 38140371059 reconstructed state.” Primary objects: q047_m15_exact_audit_v1.py, its exact-rational JSON result, the complete symbolic control including the initially warned query and corrected query, input hash checks and the four actual state JSONs. Retrieval: supplied local files and the already preserved actual raw members; independent Wolfram symbolic evaluator. DOI/arXiv: not applicable; internal project evidence.

I-PROPOSED-Q047-RUN38140371059-001: actual capture run/worker/member evidence from the earlier ingestion. Supports attribution and capture scope, not historical identity.

K-PROPOSED-Q047-BACKGROUNDCODE-001: mwt5345/class_ede, source/background.c at 5a131c91d657dd9a7c6364cc45b038710f8d0d97, SHA256 84871d25c0a29391edf8d08b4826bd3ca3b33c638dae306375c0a681bb87d451. Roles: analytic FD function 1228–1301, native moment kernel 1624–1681, initial-state/coordinate rule 2160–2354, scalar potential and units near 2980–3069. URL: https://github.com/mwt5345/class_ede/blob/5a131c91d657dd9a7c6364cc45b038710f8d0d97/source/background.c . Author legal name/year of original code publication: NOT DOCUMENTED; no invented bibliography.

K-PROPOSED-Q047-CONSTANTCODE-001: same pinned repository, include/common.h, SHA256 410ea60e5ca1de7fc501d644711fc21023fa2cbdd56dd8daede1637a3b9e900c. Role: the exact decimal _PI_ macro. URL: https://github.com/mwt5345/class_ede/blob/5a131c91d657dd9a7c6364cc45b038710f8d0d97/include/common.h . Source-defined decimals, native binary constants and mathematical pi are separate objects.

Q047_PRECURSOR_CONTRACT_V1.json: SHA256 bcd113dfd96ebba8a3e0af2b8761b679678cc00b9bafcebb414a824dcde619cc; exact original predicates, fixed equations and identity routes. Q047_RECONSTRUCTION_CONTRACT_V1.json: SHA256 958b5417b52a993d6cfcdf5bbf209fb9de6287679019e9c74ac34aa96b84c51b; authorized acquisition annex and separate reconstructed-IVP scope. Their original source IDs and complete definitions remain in the inherited journal.

Claim mapping: captured positivity/index linkage -> actual run source + M15 rational controls; moment/FD/coordinate formulas -> pinned background/common sources + M15 derivations; independent conservation/integral control -> exact Wolfram query/result; historical admission distinction -> unchanged contracts + retained M11–M14 + M15 logical scope. These are related calculations using shared inputs, not independent cosmological observations.

### Reproducibility objects

The exact audit code, result and four compact input state objects are embedded next. High-digit displays in the JSON identify deterministic arithmetic bounds/representations, not claimed physical precision. The original raw members and all 315-member provenance remain in the preserved evidence index; eight empty files retain exact zero-byte declarations. No archive is delivered.

