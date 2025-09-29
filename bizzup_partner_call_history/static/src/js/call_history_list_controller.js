/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";

export class PartnerCallHistoryListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.ui = useService("ui");
    }

    async OnUpdateCallClick() {
        try {
            this.ui.block();

            const result = await this.orm.call(
                "partner.call.history",
                "update_call_history",
                [],
                {}
            );

            const count = result ? result.length : 0;
            this.notification.add(`Assigned partner(s) to ${count} call(s).`, { type: "success" });

            await this.model.root.reload();
        } catch {
            // Silent error handling — no message or log
        } finally {
            this.ui.unblock();
        }
    }
}

registry.category("views").add("partner_call_history_list", {
    ...listView,
    Controller: PartnerCallHistoryListController,
    buttonTemplate: "bizzup_partner_call_history.ListView.Buttons",
});
