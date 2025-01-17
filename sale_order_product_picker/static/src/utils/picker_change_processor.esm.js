/** @odoo-module **/
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */
import { x2ManyCommands } from "@web/core/orm_service";

export class PickerChangeProcessor {
    constructor(waitTime, x2mList, pickerKanban) {
        this.waitTime = waitTime * 1000;
        this.changes = {};
        this.timeoutId = null;
        this.x2mList = x2mList;
        this.pickerKanban = pickerKanban;
    }

    addChange(change) {
        if (!this.changes[change.id]) {
            this.changes[change.id] = {
                qty: 0,
                pickerRecord: change.pickerRecord,
                ctx: change.ctx,
                orderLines: change.orderLines,
            };
        }
        this.changes[change.id].qty++;
        this.resetTimer();
    }

    resetTimer() {
        if (this.timeoutId !== null) {
            clearTimeout(this.timeoutId);
        }
        this.timeoutId = setTimeout(() => this.processChanges(), this.waitTime);
    }

    processChanges() {
        if (Object.keys(this.changes).length <= 0) {
            return;
        }
        const processing_div = document.createElement("div");
        processing_div.setAttribute("id", "processing_picker");
        this.pickerKanban.prepend(processing_div);
        const lineChanges = [];
        for (var key in this.changes) {
            var change = this.changes[key];
            if (!change.orderLines.length) {
                lineChanges.push([
                    x2ManyCommands.CREATE,
                    false,
                    {
                        product_id: change.pickerRecord.data.product_id,
                        product_uom_qty: change.qty * change.pickerRecord.data.unit_factor,
                    }
                ]);
            } else {
                const pickedRecord = change.orderLines[0];
                lineChanges.push([
                    x2ManyCommands.UPDATE,
                    pickedRecord.id,
                    {
                        product_uom_qty:
                            pickedRecord.data.product_uom_qty +
                            change.qty * change.pickerRecord.data.unit_factor,
                    },
                ]);
            }
        }
        const parent = this.x2mList.model.root;
        parent.update({
            order_line: lineChanges
        }).then(async () => {
            debugger
            this.x2mList.model.root.__syncData();
            this.x2mList.model.notify();
            const pickerChanges = [];
            for (var key in this.changes) {
                const change = this.changes[key];
                const orderLine = this.x2mList.records.filter(
                    (line) =>
                        line.data.product_id[0] ===
                        change.pickerRecord.data.product_id[0]
                )[0];
                pickerChanges.push({
                    operation: "UPDATE",
                    record: change.pickerRecord,
                    data: {
                        to_process: false,
                        is_in_order: true,
                        line_price_reduce: orderLine.data.price_reduce,
                        discount: orderLine.data.discount,
                    },
                });
            }
            await this.x2mList.applyCommands("picker_ids", pickerChanges);
            this.changes = {};
            this.pickerKanban.querySelector("#processing_picker").remove();
        });
    }
}
