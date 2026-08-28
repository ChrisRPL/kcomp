:- multifile core:derives/3.
:- multifile core:overrides/2.

:- discontiguous core:derives/3.
:- discontiguous core:overrides/2.

core:derives(
    rc1,
    permanent_employee(Person),
    [
        probation_ended(Person)
    ]
).

core:derives(
    rc2,
    permission(work_remotely(Person)),
    [
        permanent_employee(Person),
        manager_approved_remote_work(Person),
        security_training_completed(Person)
    ]
).

core:derives(
    rc3,
    prohibition(work_remotely(Person)),
    [
        essential_on_site_staff(Person),
        scheduled_on_site_duty(Person)
    ]
).

core:derives(
    rc4,
    permission(work_remotely(Person)),
    [
        declared_office_emergency
    ]
).

core:overrides(rc4, rc3).
