/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.pos_access = useState({ allowed: false });
        super.setup();
    },
    async checkUserPosSessionGroup() {
        const session_id = this.pos.get_order().session_id.id;
        const pos_cashier = this.pos.cashier.id;
        const result = await this.orm.call(
            "pos.session",
            'get_user_pos_session_group',
            [[session_id], pos_cashier]
        );
        this.pos_access.allowed = result;
    },
    get getPrintReportPosSession() {
        this.checkUserPosSessionGroup();
        return this.pos_access.allowed;
    },
    async printReportPosSession() {
        const session_id = this.pos.get_order().session_id.id
        const pos_cashier = this.pos.cashier.id;
        const action = await this.orm.call(
            "pos.session",
            'action_print_pos_session',
            [[session_id], pos_cashier]
        );
        this.action.doAction(action);
    }
});
