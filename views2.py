FOR /R %G IN (migrations) DO FOR %H IN ("%G\*.py") DO IF NOT "%~nxH"=="__init__.py" DEL /F /Q "%H"


A (root)
 ├── B
 │     ├── C
 │     │     └── D
 │     └── E
 └── F
 
A → CG-01-CP-01
B → CG-01-CP-01-01
C → CG-01-CP-01-01-01
D → CG-01-CP-01-01-01-01
E → CG-01-CP-01-02
F → CG-01-CP-02


def get_parent_code(instance):

    if instance.parent is None:
        return "CG-01-CP"

    parent_summary = BOQChainageExecutiveSummeryData.objects.filter(
        boq=instance.boq,
        wbs=instance.parent
    ).first()

    if parent_summary:
        return parent_summary.value

    return None
	
from django.db.models import Max

def get_next_serial(instance):

    siblings = BOQChainageExecutiveSummeryData.objects.filter(
        boq=instance.boq,
        wbs__parent=instance.parent
    )

    last_value = siblings.aggregate(Max('value'))['value__max']

    if last_value:
        last_serial = int(last_value.split('-')[-1])
        next_serial = last_serial + 1
    else:
        next_serial = 1

    return f"{next_serial:02d}"
	
def generate_chainage_code(instance):

    base_code = "CG-01-CP"

    # ROOT LEVEL
    if instance.parent is None:

        roots = BOQChainageExecutiveSummeryData.objects.filter(
            boq=instance.boq,
            wbs__parent__isnull=True
        )

        last_value = roots.aggregate(Max('value'))['value__max']

        if last_value:
            last_serial = int(last_value.split('-')[-1])
            next_serial = last_serial + 1
        else:
            next_serial = 1

        return f"{base_code}-{next_serial:02d}"

    # CHILD LEVEL (any depth)
    parent_code = get_parent_code(instance)
    next_serial = get_next_serial(instance)
    return f"{parent_code}-{next_serial}"
