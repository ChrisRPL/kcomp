:- module(priorities, [
    defeated/3
]).

:- use_module(core).

% A rule is defeated in a case if there is a higher-priority rule 
% that overrides it, and that higher-priority rule's conditions are proven.
defeated(Case, Rule, _{type: defeated_by, higher_rule: HigherRule, traces: DefeatingTraces}) :-
    overrides(HigherRule, Rule),
    derives(HigherRule, _, Conditions),
    all_proven(Case, Conditions, DefeatingTraces).
