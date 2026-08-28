import janus_swi as janus
from tests.test_pilot_cases import setup_prolog, add_fact
setup_prolog()
janus.query_once("retractall(core:case_fact(_,_,_))")
add_fact("carol", "declared_office_emergency", True)

res = janus.query_once("priorities:defeated(carol, rc3)")
print("Is rc3 defeated?", res)
