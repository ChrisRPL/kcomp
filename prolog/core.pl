:- module(core, [
    proves/3,
    case_fact/3,
    derives/3,
    overrides/2,
    all_proven/3
]).

:- dynamic case_fact/3.
:- dynamic derives/3.
:- dynamic overrides/2.

:- use_module(priorities).

% Base case: explicit positive fact in the case
proves(Case, P, _{type: fact, fact: P, polarity: positive}) :-
    case_fact(Case, P, positive).

% Base case: explicit negative fact in the case
proves(Case, neg(P), _{type: fact, fact: P, polarity: negative}) :-
    case_fact(Case, P, negative).

% Inductive case: Rule derives P
proves(Case, P, _{type: proof, rule: Rule, traces: Traces}) :-
    derives(Rule, P, Conditions),
    all_proven(Case, Conditions, Traces),
    \+ defeated(Case, Rule, _).

% Deontic mappings: prohibition implies neg(permission)
proves(Case, neg(permission(P)), _{type: deontic, source: prohibition, trace: Trace}) :-
    proves(Case, prohibition(P), Trace).

% Deontic mappings: permission implies neg(prohibition)
proves(Case, neg(prohibition(P)), _{type: deontic, source: permission, trace: Trace}) :-
    proves(Case, permission(P), Trace).

% Helper: Check if all conditions are proven for a rule, accumulating traces
all_proven(_, [], []).
all_proven(Case, [Cond|Rest], [Trace|TraceRest]) :-
    proves(Case, Cond, Trace),
    all_proven(Case, Rest, TraceRest).

