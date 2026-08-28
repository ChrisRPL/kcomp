:- module(core, [
    proves/2,
    case_fact/3,
    derives/3,
    overrides/2,
    all_proven/2
]).

:- dynamic case_fact/3.
:- dynamic derives/3.
:- dynamic overrides/2.

:- use_module(priorities).

% Base case: explicit positive fact in the case
proves(Case, P) :-
    case_fact(Case, P, positive).

% Base case: explicit negative fact in the case
proves(Case, neg(P)) :-
    case_fact(Case, P, negative).

% Inductive case: Rule derives P
proves(Case, P) :-
    derives(Rule, P, Conditions),
    all_proven(Case, Conditions),
    \+ defeated(Case, Rule).

% Inductive case: Rule derives negative conclusion (e.g. prohibition)
proves(Case, neg(P)) :-
    derives(Rule, prohibition(P), Conditions),
    all_proven(Case, Conditions),
    \+ defeated(Case, Rule).

% Helper: Check if all conditions are proven for a rule
all_proven(_, []).
all_proven(Case, [Cond|Rest]) :-
    proves(Case, Cond),
    all_proven(Case, Rest).
