/** @odoo-module **/

import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(CalendarFilterPanel.prototype, {
    async loadSource(section, request) {
        const resModel = this.props.model.fields[section.fieldName].relation;
        const domain = [
            ["id", "not in", section.filters.filter((f) => f.type !== "all").map((f) => f.value)],
            ['user_ids.employee_ids', '!=', false], //Custom Domain to display only employees from all contact's
        ];
        const records = await this.orm.call(resModel, "name_search", [], {
            name: request,
            operator: "ilike",
            args: domain,
            limit: 8,
            context: {},
        });

        const options = records.map((result) => ({
            value: result[0],
            label: result[1],
            model: resModel,
        }));

        if (records.length > 7) {
            options.push({
                label: _t("Search More..."),
                action: () => this.onSearchMore(section, resModel, domain, request),
                classList: "o_calendar_dropdown_option",
            });
        }

        if (records.length === 0) {
            options.push({
                label: _t("No records"),
                classList: "o_m2o_no_result",
                unselectable: true,
            });
        }

        return options;
    },
});
