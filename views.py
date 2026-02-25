
def get_root_wbs(wbs):
    while wbs.parent is not None:
        wbs = wbs.parent
    return wbs


@receiver(post_save, sender=WBSList)
def signal_update_wbs_list(sender, instance, created, **kwargs):

    if not created or not instance.boq:
        return

    # 🔹 Find Root WBS (Top Most Parent)
    root_wbs = get_root_wbs(instance)

    # 🔹 Case 1: If this is root itself
    if instance == root_wbs:

        BOQChainage.objects.get_or_create(
            boq=instance.boq,
            wbs=instance,
            organization=instance.organization,
            defaults={
                "name": f"CH-{instance.boq.id}-{instance.pk}",
                "start": 0,
                "end": 1,
            }
        )

    # 🔹 Case 2: If this is child (any level)
    else:

        # Get root chainage
        parent_chainage = BOQChainage.objects.filter(
            boq=instance.boq,
            wbs=root_wbs
        ).first()

        if parent_chainage:
            auto_value = generate_chainage_code(instance)

            BOQChainageExecutiveSummeryData.objects.get_or_create(
                boq=instance.boq,
                wbs=instance,
                form=parent_chainage,
                defaults={
                    "organization": instance.organization,
                    "type": "C",
                    "value": auto_value,
                }
            )
