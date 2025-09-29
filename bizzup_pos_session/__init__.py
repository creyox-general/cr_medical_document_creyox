# -*- coding: utf-8 -*-
from . import models


def post_init(env):
    """Company write"""
    report = env.ref("point_of_sale.sale_details_report",
                     raise_if_not_found=False)
    group = env.ref(
        "bizzup_pos_session.group_allow_all_user_from_pos_session",
        raise_if_not_found=False,
    )

    if report and group:
        report.groups_id = [(4, group.id)]
