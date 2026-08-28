:- module(truth_status, [
    truth_status/3
]).

:- use_module(core).

% Evaluates the four-valued truth status of P in Case.
% Returns a dict with {status: Status, trace_positive: T1, trace_negative: T2}.

truth_status(Case, P, Result) :-
    % Check if P is proven
    (   proves(Case, P, TracePosTerm)
    ->  Proven = true, term_string(TracePosTerm, TracePos)
    ;   Proven = false, TracePos = null
    ),
    % Check if neg(P) is proven
    (   proves(Case, neg(P), TraceNegTerm)
    ->  Refuted = true, term_string(TraceNegTerm, TraceNeg)
    ;   Refuted = false, TraceNeg = null
    ),
    % Determine the final 4-valued status
    (   Proven == true, Refuted == true
    ->  Status = conflict
    ;   Proven == true, Refuted == false
    ->  Status = proven
    ;   Proven == false, Refuted == true
    ->  Status = refuted
    ;   Status = unknown
    ),
    Result = _{status: Status, trace_positive: TracePos, trace_negative: TraceNeg}.
