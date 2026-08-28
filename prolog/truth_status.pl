:- module(truth_status, [
    status/3
]).

:- use_module(core).

% Evaluates the 4-valued logic status of a proposition P in Case
status(Case, P, proven) :-
    proves(Case, P),
    \+ proves(Case, neg(P)).

status(Case, P, refuted) :-
    \+ proves(Case, P),
    proves(Case, neg(P)).

status(Case, P, unknown) :-
    \+ proves(Case, P),
    \+ proves(Case, neg(P)).

status(Case, P, conflict) :-
    proves(Case, P),
    proves(Case, neg(P)).
