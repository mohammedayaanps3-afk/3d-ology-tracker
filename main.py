import flet as ft
import json
import os
import asyncio
from datetime import datetime

VERSION = "2.3.0"

BG = "#10151D"
PANEL = "#1A2430"
PANEL_DARK = "#151E28"
PANEL_LIGHT = "#253443"
ORANGE = "#FF8A32"
CYAN = "#36C9E8"
WHITE = "#F1F5F9"
MUTED = "#9AAABA"
GREEN = "#43D19E"
RED = "#FF6577"
YELLOW = "#F5C451"

STATUSES = ["New", "Queued", "Printing", "Ready", "Collected"]
STATUS_COLORS = {
    "New": CYAN,
    "Queued": YELLOW,
    "Printing": ORANGE,
    "Ready": GREEN,
    "Collected": MUTED,
}


def next_id(items):
    return max([item.get("id", 0) for item in items] + [0]) + 1


async def main(page: ft.Page):
    page.title = "3D-Ology Order Tracker | 3D-Ology Workshop"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    # Persistent storage path on Android / PC
    storage_dir = os.getenv("FLET_APP_STORAGE_DATA") or os.path.join(os.path.expanduser("~"), "3D-Ology-Tracker")
    os.makedirs(storage_dir, exist_ok=True)
    data_file = os.path.join(storage_dir, "nuvi_lx_data.json")

    state = {"customers": [], "orders": [], "edit_cust_id": None, "edit_order_id": None}

    def load_data():
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    state["customers"] = data.get("customers", [])
                    state["orders"] = data.get("orders", [])
            except Exception:
                pass

    def save_data():
        try:
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump({"customers": state["customers"], "orders": state["orders"]}, f, indent=4)
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Save error: {e}"), bgcolor=RED)
            page.snack_bar.open = True
            page.update()

    def customer_name(cid):
        for c in state["customers"]:
            if c["id"] == cid:
                return c["name"]
        return "Unknown customer"

    load_data()

    # -----------------------------------------------------
    # 5-SECOND SPLASH SCREEN
    # -----------------------------------------------------
    splash_view = ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        bgcolor=BG,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Image(src="Splash.jpg", width=680, height=380, fit=ft.ImageFit.CONTAIN, border_radius=12),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ProgressRing(width=22, height=22, stroke_width=3, color=ORANGE),
                        ft.Text("LOADING 3D-OLOGY ORDER TRACKER...", color=WHITE, weight=ft.FontWeight.BOLD, size=13),
                    ],
                ),
            ],
        ),
    )
    page.add(splash_view)
    page.update()
    await asyncio.sleep(5)
    page.controls.clear()

    # -----------------------------------------------------
    # HEADER & CLOCK
    # -----------------------------------------------------
    clock_text = ft.Text("", color=ORANGE, weight=ft.FontWeight.BOLD, size=12)

    async def update_clock():
        while True:
            clock_text.value = datetime.now().strftime("%A, %d %B %Y   •   %I:%M:%S %p")
            try:
                clock_text.update()
            except Exception:
                break
            await asyncio.sleep(1)

    header = ft.Container(
        padding=ft.padding.only(bottom=10),
        border=ft.border.only(bottom=ft.BorderSide(2, ORANGE)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("3D-Ology Order Tracker", color=ORANGE, size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("3D-OLOGY WORKSHOP SYSTEM", color=MUTED, size=11, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                    spacing=2,
                    controls=[
                        ft.Text("WORKSHOP CONTROL PANEL", color=CYAN, size=11, weight=ft.FontWeight.BOLD),
                        ft.Text(f"OFFLINE EDITION  |  VERSION {VERSION}", color=MUTED, size=10),
                        clock_text,
                    ],
                ),
            ],
        ),
    )

    # -----------------------------------------------------
    # DASHBOARD TAB
    # -----------------------------------------------------
    val_customers = ft.Text("0", color=CYAN, size=28, weight=ft.FontWeight.BOLD)
    val_orders = ft.Text("0", color=ORANGE, size=28, weight=ft.FontWeight.BOLD)
    val_active = ft.Text("0", color=YELLOW, size=28, weight=ft.FontWeight.BOLD)
    val_ready = ft.Text("0", color=GREEN, size=28, weight=ft.FontWeight.BOLD)

    def make_stat_card(title, val_ctrl, accent):
        return ft.Container(
            expand=True,
            bgcolor=PANEL,
            border_radius=8,
            border=ft.border.all(1, PANEL_LIGHT),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Container(height=4, bgcolor=accent),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(title, color=MUTED, size=11, weight=ft.FontWeight.BOLD),
                                val_ctrl,
                            ],
                        ),
                    ),
                ],
            ),
        )

    recent_table = ft.DataTable(
        bgcolor=PANEL_DARK,
        heading_row_color=PANEL_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("ORDER #", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("CUSTOMER", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("PRODUCT", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("QTY", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("STATUS", color=CYAN, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
    )

    # -----------------------------------------------------
    # CUSTOMERS TAB
    # -----------------------------------------------------
    cust_name_in = ft.TextField(label="Customer Name", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    cust_grade_in = ft.TextField(label="Grade", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    cust_notes_in = ft.TextField(label="Notes", multiline=True, min_lines=2, bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    cust_search_in = ft.TextField(label="Search customers...", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)

    cust_table = ft.DataTable(
        bgcolor=PANEL_DARK,
        heading_row_color=PANEL_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("ID", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("NAME", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("GRADE", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ORDERS", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ACTIONS", color=CYAN, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
    )

    def clear_cust_form(e=None):
        state["edit_cust_id"] = None
        cust_name_in.value = ""
        cust_grade_in.value = ""
        cust_notes_in.value = ""
        page.update()

    def save_cust(e):
        name = (cust_name_in.value or "").strip()
        if not name:
            return
        grade = (cust_grade_in.value or "").strip()
        notes = (cust_notes_in.value or "").strip()

        if state["edit_cust_id"] is None:
            state["customers"].append({"id": next_id(state["customers"]), "name": name, "grade": grade, "notes": notes})
        else:
            for c in state["customers"]:
                if c["id"] == state["edit_cust_id"]:
                    c.update({"name": name, "grade": grade, "notes": notes})
        save_data()
        clear_cust_form()
        refresh_all()

    def edit_cust_click(cid):
        for c in state["customers"]:
            if c["id"] == cid:
                state["edit_cust_id"] = cid
                cust_name_in.value = c.get("name", "")
                cust_grade_in.value = c.get("grade", "")
                cust_notes_in.value = c.get("notes", "")
                page.update()

    def delete_cust_click(cid):
        if any(o.get("customer_id") == cid for o in state["orders"]):
            page.snack_bar = ft.SnackBar(ft.Text("Cannot delete customer with active orders!"), bgcolor=RED)
            page.snack_bar.open = True
            page.update()
            return
        state["customers"] = [c for c in state["customers"] if c["id"] != cid]
        save_data()
        refresh_all()

    # -----------------------------------------------------
    # ORDERS TAB
    # -----------------------------------------------------
    ord_cust_dd = ft.Dropdown(label="Customer", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_prod_in = ft.TextField(label="Product", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_qty_in = ft.TextField(label="Quantity", value="1", keyboard_type=ft.KeyboardType.NUMBER, bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_col_in = ft.TextField(label="Colour", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_due_in = ft.TextField(label="Due Date", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_status_dd = ft.Dropdown(
        label="Status",
        value="New",
        bgcolor=PANEL_DARK,
        border_color=PANEL_LIGHT,
        options=[ft.dropdown.Option(s) for s in STATUSES],
    )
    ord_notes_in = ft.TextField(label="Notes", multiline=True, min_lines=2, bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)
    ord_search_in = ft.TextField(label="Search orders...", bgcolor=PANEL_DARK, border_color=PANEL_LIGHT)

    ord_table = ft.DataTable(
        bgcolor=PANEL_DARK,
        heading_row_color=PANEL_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("#", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("CUSTOMER", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("PRODUCT", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("QTY", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("COLOUR", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("STATUS", color=CYAN, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ACTIONS", color=CYAN, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
    )

    def clear_ord_form(e=None):
        state["edit_order_id"] = None
        ord_prod_in.value = ""
        ord_qty_in.value = "1"
        ord_col_in.value = ""
        ord_due_in.value = ""
        ord_status_dd.value = "New"
        ord_notes_in.value = ""
        page.update()

    def save_ord(e):
        if not ord_cust_dd.value or not (ord_prod_in.value or "").strip():
            return
        cid = int(ord_cust_dd.value)
        try:
            qty = max(1, int(ord_qty_in.value or 1))
        except ValueError:
            qty = 1

        payload = {
            "customer_id": cid,
            "product": ord_prod_in.value.strip(),
            "quantity": qty,
            "colour": (ord_col_in.value or "").strip(),
            "due_date": (ord_due_in.value or "").strip(),
            "status": ord_status_dd.value or "New",
            "notes": (ord_notes_in.value or "").strip(),
        }
        if state["edit_order_id"] is None:
            payload["id"] = next_id(state["orders"])
            state["orders"].append(payload)
        else:
            for o in state["orders"]:
                if o["id"] == state["edit_order_id"]:
                    o.update(payload)
        save_data()
        clear_ord_form()
        refresh_all()

    def edit_ord_click(oid):
        for o in state["orders"]:
            if o["id"] == oid:
                state["edit_order_id"] = oid
                ord_cust_dd.value = str(o.get("customer_id", ""))
                ord_prod_in.value = o.get("product", "")
                ord_qty_in.value = str(o.get("quantity", 1))
                ord_col_in.value = o.get("colour", "")
                ord_due_in.value = o.get("due_date", "")
                ord_status_dd.value = o.get("status", "New")
                ord_notes_in.value = o.get("notes", "")
                page.update()

    def delete_ord_click(oid):
        state["orders"] = [o for o in state["orders"] if o["id"] != oid]
        save_data()
        refresh_all()

    # -----------------------------------------------------
    # REFRESH ALL VIEWS
    # -----------------------------------------------------
    def refresh_all(e=None):
        val_customers.value = str(len(state["customers"]))
        val_orders.value = str(len(state["orders"]))
        val_active.value = str(sum(1 for o in state["orders"] if o.get("status") not in ("Ready", "Collected")))
        val_ready.value = str(sum(1 for o in state["orders"] if o.get("status") == "Ready"))

        # Recent orders table
        recent_table.rows.clear()
        for o in sorted(state["orders"], key=lambda x: x.get("id", 0), reverse=True)[:10]:
            st = o.get("status", "New")
            recent_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(o["id"]))),
                        ft.DataCell(ft.Text(customer_name(o.get("customer_id")))),
                        ft.DataCell(ft.Text(o.get("product", ""))),
                        ft.DataCell(ft.Text(str(o.get("quantity", 1)))),
                        ft.DataCell(ft.Text(st, color=STATUS_COLORS.get(st, WHITE), weight=ft.FontWeight.BOLD)),
                    ]
                )
            )

        # Customer dropdown & table
        ord_cust_dd.options = [ft.dropdown.Option(key=str(c["id"]), text=f"{c['id']} - {c['name']}") for c in state["customers"]]
        if ord_cust_dd.options and not ord_cust_dd.value:
            ord_cust_dd.value = ord_cust_dd.options[0].key

        c_query = (cust_search_in.value or "").lower()
        cust_table.rows.clear()
        for c in state["customers"]:
            if c_query and c_query not in f"{c['name']} {c.get('grade', '')}".lower():
                continue
            ocount = sum(1 for o in state["orders"] if o.get("customer_id") == c["id"])
            cid = c["id"]
            cust_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(cid))),
                        ft.DataCell(ft.Text(c["name"])),
                        ft.DataCell(ft.Text(c.get("grade", ""))),
                        ft.DataCell(ft.Text(str(ocount))),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(ft.Icons.EDIT, icon_color=CYAN, on_click=lambda e, i=cid: edit_cust_click(i)),
                                    ft.IconButton(ft.Icons.DELETE, icon_color=RED, on_click=lambda e, i=cid: delete_cust_click(i)),
                                ],
                            )
                        ),
                    ]
                )
            )

        # Orders table
        o_query = (ord_search_in.value or "").lower()
        ord_table.rows.clear()
        for o in sorted(state["orders"], key=lambda x: x.get("id", 0), reverse=True):
            cname = customer_name(o.get("customer_id"))
            st = o.get("status", "New")
            if o_query and o_query not in f"{o['id']} {cname} {o.get('product', '')} {o.get('colour', '')} {st}".lower():
                continue
            oid = o["id"]
            ord_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(oid))),
                        ft.DataCell(ft.Text(cname)),
                        ft.DataCell(ft.Text(o.get("product", ""))),
                        ft.DataCell(ft.Text(str(o.get("quantity", 1)))),
                        ft.DataCell(ft.Text(o.get("colour", ""))),
                        ft.DataCell(ft.Text(st, color=STATUS_COLORS.get(st, WHITE), weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(ft.Icons.EDIT, icon_color=CYAN, on_click=lambda e, i=oid: edit_ord_click(i)),
                                    ft.IconButton(ft.Icons.DELETE, icon_color=RED, on_click=lambda e, i=oid: delete_ord_click(i)),
                                ],
                            )
                        ),
                    ]
                )
            )

        page.update()

    cust_search_in.on_change = refresh_all
    ord_search_in.on_change = refresh_all

    # -----------------------------------------------------
    # TABS LAYOUT
    # -----------------------------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        indicator_color=ORANGE,
        label_color=ORANGE,
        unselected_label_color=MUTED,
        tabs=[
            ft.Tab(
                text="DASHBOARD",
                content=ft.Container(
                    padding=ft.padding.only(top=14),
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Row(
                                spacing=12,
                                controls=[
                                    make_stat_card("CUSTOMERS", val_customers, CYAN),
                                    make_stat_card("TOTAL ORDERS", val_orders, ORANGE),
                                    make_stat_card("ACTIVE JOBS", val_active, YELLOW),
                                    make_stat_card("READY TO COLLECT", val_ready, GREEN),
                                ],
                            ),
                            ft.Container(
                                bgcolor=PANEL,
                                padding=14,
                                border_radius=8,
                                border=ft.border.all(1, PANEL_LIGHT),
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            controls=[
                                                ft.Text("RECENT WORKSHOP ORDERS", color=CYAN, weight=ft.FontWeight.BOLD),
                                                ft.ElevatedButton("Refresh", bgcolor=PANEL_LIGHT, color=WHITE, on_click=refresh_all),
                                            ],
                                        ),
                                        ft.Row([recent_table], scroll=ft.ScrollMode.AUTO),
                                    ]
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            ft.Tab(
                text="CUSTOMERS",
                content=ft.Container(
                    padding=ft.padding.only(top=14),
                    content=ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"sm": 12, "md": 4},
                                bgcolor=PANEL,
                                padding=14,
                                border_radius=8,
                                content=ft.Column(
                                    spacing=10,
                                    controls=[
                                        ft.Text("CUSTOMER DETAILS", color=ORANGE, weight=ft.FontWeight.BOLD),
                                        cust_name_in,
                                        cust_grade_in,
                                        cust_notes_in,
                                        ft.ElevatedButton("SAVE CUSTOMER", bgcolor=ORANGE, color=BG, on_click=save_cust, width=400),
                                        ft.ElevatedButton("CLEAR FORM", bgcolor=PANEL_LIGHT, color=WHITE, on_click=clear_cust_form, width=400),
                                    ],
                                ),
                            ),
                            ft.Container(
                                col={"sm": 12, "md": 8},
                                bgcolor=PANEL,
                                padding=14,
                                border_radius=8,
                                content=ft.Column(
                                    spacing=10,
                                    controls=[
                                        cust_search_in,
                                        ft.Row([cust_table], scroll=ft.ScrollMode.AUTO),
                                    ],
                                ),
                            ),
                        ]
                    ),
                ),
            ),
            ft.Tab(
                text="ORDERS",
                content=ft.Container(
                    padding=ft.padding.only(top=14),
                    content=ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"sm": 12, "md": 4},
                                bgcolor=PANEL,
                                padding=14,
                                border_radius=8,
                                content=ft.Column(
                                    spacing=10,
                                    controls=[
                                        ft.Text("PRINT JOB DETAILS", color=ORANGE, weight=ft.FontWeight.BOLD),
                                        ord_cust_dd,
                                        ord_prod_in,
                                        ord_qty_in,
                                        ord_col_in,
                                        ord_due_in,
                                        ord_status_dd,
                                        ord_notes_in,
                                        ft.ElevatedButton("SAVE ORDER", bgcolor=ORANGE, color=BG, on_click=save_ord, width=400),
                                        ft.ElevatedButton("CLEAR FORM", bgcolor=PANEL_LIGHT, color=WHITE, on_click=clear_ord_form, width=400),
                                    ],
                                ),
                            ),
                            ft.Container(
                                col={"sm": 12, "md": 8},
                                bgcolor=PANEL,
                                padding=14,
                                border_radius=8,
                                content=ft.Column(
                                    spacing=10,
                                    controls=[
                                        ord_search_in,
                                        ft.Row([ord_table], scroll=ft.ScrollMode.AUTO),
                                    ],
                                ),
                            ),
                        ]
                    ),
                ),
            ),
        ],
    )

    footer = ft.Container(
        padding=ft.padding.only(top=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("3D-OLOGY  •  PRINT SMART. CREATE MORE.", color=MUTED, size=10, weight=ft.FontWeight.BOLD),
                ft.Text("LOCAL DATA STORAGE", color=GREEN, size=10, weight=ft.FontWeight.BOLD),
            ],
        ),
    )

    page.add(header, tabs, footer)
    refresh_all()
    asyncio.create_task(update_clock())


ft.app(target=main, assets_dir="assets")
