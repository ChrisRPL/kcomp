import janus_swi as janus
from tests.test_pilot_cases import setup_prolog, add_fact
setup_prolog()
janus.query_once("retractall(core:case_fact(_,_,_))")
add_fact("carol", "declared_office_emergency", True)

print(janus.query_once("core:case_fact(carol, declared_office_emergency, positive)"))
print(janus.query_once("core:proves(carol, declared_office_emergency)"))
