:- module(priorities, [
    defeated/2
]).

:- use_module(core).

% A rule is defeated in a case if there is a higher-priority rule 
% that overrides it, and that higher-priority rule's conditions are proven.
defeated(Case, Rule) :-
    overrides(HigherRule, Rule),
    derives(HigherRule, _, Conditions),
    all_proven(Case, Conditions).
