import janus_swi as janus
from tests.test_pilot_cases import setup_prolog, add_fact
setup_prolog()
janus.query_once("retractall(core:case_fact(_,_,_))")
add_fact("carol", "probation_ended(carol)", True)
add_fact("carol", "manager_approved_remote_work(carol)", True)
add_fact("carol", "security_training_completed(carol)", True)
add_fact("carol", "essential_on_site_staff(carol)", True)
add_fact("carol", "scheduled_on_site_duty(carol)", True)
add_fact("carol", "declared_office_emergency", True)

res1 = list(janus.query("core:derives(Rule, Concl, Conds)"))
print("All rules:", res1)

res2 = list(janus.query("priorities:defeated(carol, rc3)"))
print("Is rc3 defeated?", res2)

res3 = list(janus.query("core:proves(carol, prohibition(work_remotely(carol)))"))
print("Is prohibition proven?", res3)
